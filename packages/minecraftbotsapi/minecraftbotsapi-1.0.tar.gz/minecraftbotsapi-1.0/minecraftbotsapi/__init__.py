# -*- coding: utf-8 -*-
"""
Minecraft Bot Framework (Python ⇄ Node.js ⇄ Mineflayer)
======================================================

Автор: FLORESTDEV (/florestdev/minecraftbotsapi)
Версия: 1.0

Описание
--------
Данная библиотека позволяет создавать и управлять Minecraft-ботами
на Python, используя Node.js и библиотеку mineflayer.

Python выступает как управляющий слой (AI, логика, реакции),
Node.js — как Minecraft-клиент.

Архитектура
-----------
Python <-> STDIN / STDOUT (JSON) <-> Node.js (mineflayer) <-> Minecraft Server

Возможности
-----------
- Подключение бота к серверу
- Отправка сообщений в чат
- Подписка на события (чат, кик, атака, статус)
- Follow / StopFollow игрока
- Приветственные сообщения
- Безопасное завершение процесса

Требования
----------
- Python 3.10+
- Node.js 18+
- npm install mineflayer

"""

from __future__ import annotations

import subprocess
import threading
import json
import time
import random
import os
from typing import Callable, Dict, Optional

# ---------------------------------------------------------------------------
# Node.js код mineflayer-бота
# ---------------------------------------------------------------------------

NODE_JS_CODE = """
const mineflayer = require('mineflayer');
const readline = require('readline');

const args = process.argv.slice(2);

if (args.length < 3) {
  console.log('Usage: node bot.js <host> [port] <username> <version>');
  process.exit(1);
}

let host, port, username, version;

if (args.length === 3) {
  [host, username, version] = args;
} else {
  [host, port, username, version] = args;
  port = parseInt(port);
}

const options = { host, username, version };
if (port) options.port = port;

const bot = mineflayer.createBot(options);

function send(obj) {
  process.stdout.write(JSON.stringify(obj) + '\n');
}

bot.once('login', () => {
  send({ type: 'status', message: `Bot ${bot.username} logged in` });
});

bot.on('chat', (username, message) => {
  send({ type: 'chat', user: username, message });
});

bot.on('kicked', reason => {
  send({ type: 'kicked', reason: reason.toString() });
  process.exit(0);
});

bot.on('end', () => {
  send({ type: 'end' });
  process.exit(0);
});

bot.on('error', err => {
  send({ type: 'error', message: err.message });
});

let followTarget = null;
let followTimer = null;

function startFollow(playerName) {
  followTarget = playerName;
  if (followTimer) clearInterval(followTimer);

  followTimer = setInterval(() => {
    const target = bot.players[followTarget]?.entity;
    if (!target) return;

    const pos = target.position.offset(0, 1.6, 0);
    bot.lookAt(pos, true);
    bot.setControlState('forward', true);
  }, 200);

  send({ type: 'status', message: `Following ${playerName}` });
}

function stopFollow() {
  followTarget = null;
  if (followTimer) clearInterval(followTimer);
  followTimer = null;
  bot.setControlState('forward', false);
  send({ type: 'status', message: 'Follow stopped' });
}

const rl = readline.createInterface({ input: process.stdin });

rl.on('line', line => {
  try {
    const cmd = JSON.parse(line);

    switch (cmd.action) {
      case 'chat':
        bot.chat(cmd.text);
        break;
      case 'follow':
        startFollow(cmd.player);
        break;
      case 'stopFollow':
        stopFollow();
        break;
      case 'quit':
        bot.quit();
        process.exit(0);
    }
  } catch (e) {
    send({ type: 'error', message: e.message });
  }
});
"""

# ---------------------------------------------------------------------------
# Python API
# ---------------------------------------------------------------------------

EventHandler = Callable[..., None]


class MinecraftBot:
    """
    Главный класс управления Minecraft-ботом.

    Пример:
    -------
    >>> bot = MinecraftBot(
    ...     node_path='node',
    ...     bot_js_path='./bot.js',
    ...     host='localhost',
    ...     username='PythonBot',
    ...     version='1.20.1'
    ... )
    >>> bot.on('chat', lambda u, m: print(u, m))
    >>> bot.start()
    """

    def __init__(
        self,
        node_path: str,
        bot_js_path: str,
        host: str,
        username: str,
        version: str,
        port: Optional[int] = None,
        welcome_messages: Optional[list[str]] = None,
    ):
        self.node_path = node_path
        self.bot_js_path = bot_js_path
        self.host = host
        self.port = port
        self.username = username
        self.version = version
        self.welcome_messages = welcome_messages or []

        self.process: Optional[subprocess.Popen] = None
        self.handlers: Dict[str, EventHandler] = {}

        self._prepare_bot_js()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Запускает Node.js процесс и подключает бота."""
        args = [self.node_path, self.bot_js_path, self.host]
        if self.port:
            args.append(str(self.port))
        args.extend([self.username, self.version])

        self.process = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        threading.Thread(target=self._reader, daemon=True).start()
        threading.Thread(target=self._send_welcome, daemon=True).start()

    def stop(self) -> None:
        """Корректно останавливает бота."""
        if self.process and self.process.poll() is None:
            self._send({'action': 'quit'})
            time.sleep(0.2)
            self.process.kill()

    def chat(self, text: str) -> None:
        """Отправить сообщение в чат."""
        self._send({'action': 'chat', 'text': text})

    def follow(self, player: str) -> None:
        """Следовать за игроком."""
        self._send({'action': 'follow', 'player': player})

    def stop_follow(self) -> None:
        """Остановить следование."""
        self._send({'action': 'stopFollow'})

    def on(self, event: str, handler: EventHandler) -> None:
        """Зарегистрировать обработчик события."""
        self.handlers[event] = handler

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _prepare_bot_js(self) -> None:
        os.makedirs(os.path.dirname(self.bot_js_path) or '.', exist_ok=True)
        if not os.path.exists(self.bot_js_path):
            with open(self.bot_js_path, 'w', encoding='utf-8') as f:
                f.write(NODE_JS_CODE)

    def _send(self, data: dict) -> None:
        if not self.process or self.process.poll() is not None:
            return
        try:
            self.process.stdin.write(json.dumps(data) + '\n')
            self.process.stdin.flush()
        except Exception:
            pass

    def _reader(self) -> None:
        assert self.process and self.process.stdout
        for line in self.process.stdout:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            event_type = event.get('type')
            handler = self.handlers.get(event_type)
            if handler:
                try:
                    handler(**{k: v for k, v in event.items() if k != 'type'})
                except Exception:
                    pass

    def _send_welcome(self) -> None:
        time.sleep(1)
        for msg in self.welcome_messages:
            self.chat(msg)
            time.sleep(random.uniform(0.8, 1.5))
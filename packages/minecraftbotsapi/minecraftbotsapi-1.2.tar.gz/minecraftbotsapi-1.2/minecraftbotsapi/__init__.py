# -*- coding: utf-8 -*-
"""
Minecraft Bot Framework (Python ⇄ Node.js ⇄ Mineflayer)
======================================================

Автор: FLORESTDEV (/florestdev/minecraftbotsapi)
Версия: 1.2

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

from __future__ import annotations

import subprocess
import threading
import json
import time
import os
import random
from typing import Callable, Dict, Optional

NODE_JS_CODE = """
// bot.js
const mineflayer = require('mineflayer');
const readline = require('readline');

// Аргументы: host, [port], username, version
const args = process.argv.slice(2);

if (args.length < 3) {
  console.log('Использование: node bot.js <host> [port] <username> <version>');
  process.exit(1);
}

let host, port, username, version;

if (args.length === 3) {
  [host, username, version] = args;
  port = null;
} else if (args.length === 4) {
  [host, port, username, version] = args;
  port = parseInt(port);
}

let exited = false;
function exitOnce() {
  if (exited) return;
  exited = true;
  process.exit(0);
}

// Создание бота
const botOptions = { host, username, version };
if (port) botOptions.port = port;

const bot = mineflayer.createBot(botOptions);

function send(obj) {
  let json = JSON.stringify(obj);

  // Разбиваем на части по 1000 символов
  const chunkSize = 1000;
  for (let i = 0; i < json.length; i += chunkSize) {
    process.stdout.write(json.slice(i, i + chunkSize) + "\n");
  }
}

let wanderInterval = null;

function startWandering() {
  // Если уже есть интервал, убираем старый
  if (wanderInterval) clearInterval(wanderInterval);

  // Каждые 1.5 секунды случайно меняем направление
  wanderInterval = setInterval(() => {
    // Выбираем случайный угол поворота в радианах
    const angle = Math.random() * 2 * Math.PI;
    const botPos = bot.entity.position;
    const targetPos = botPos.offset(Math.cos(angle), 0, Math.sin(angle));

    // Смотрим в сторону точки
    bot.lookAt(targetPos, true);

    // Включаем движение вперёд
    bot.setControlState('forward', true);
  }, 1500);

  send({ type: 'status', msg: 'Бот начал просто ходить' });
}

// -------------------- События --------------------

bot.on('login', () => {
  send({ type: 'status', msg: `Бот ${bot.username} подключился` });
  startWandering();
});


// Стандартный чат
bot.on('chat', (user, message) =>
  send({ type: 'chat', user, message })
);


bot.on('playerCollect', (collector, itemDrop) => {
  if (collector === bot.entity) {
    console.log(`Бот подобрал: ${itemDrop.name}`);
    send({ type: 'collected', item: itemDrop.name });
    // Выбрасываем предмет сразу после подбора
    const slot = bot.inventory.findInventoryItem(itemDrop.type, null);
    if (slot) {
      bot.tossStack(slot, err => {
        if (err) console.log('Ошибка при выбрасывании:', err.message);
        else console.log(`${itemDrop.name} выброшен`);
      });
    }
  }
});



// Ловим все сообщения, включая плагины
bot.on('message', (jsonMsg) => {
  try {
    const text = jsonMsg.toString().trim();
    if (!text) return;

    // Пробуем вытянуть ник и сообщение из <ник> сообщение
    let user = null;
    let message = text;

    const match = text.match(/^<(.+?)>\s(.+)$/); // для формата <ник> текст
    if (match) {
      user = match[1];
      message = match[2];
    }

    send({ type: 'chat', user, message, raw: text });
  } catch (e) {
    send({ type: 'error', msg: '[MESSAGE PARSE ERROR] ' + e.message });
  }
});

// Получение урона
bot.on('entityHurt', (entity, attacker) => {
  if (entity === bot.entity && attacker) {
    send({ type: 'attacked', by: attacker.username });
  }
});

bot.on('kicked', reason => {
  send({ type: 'kicked', reason: reason.toString() });
  exitOnce();
});

bot.on('end', () => {
  send({ type: 'end', msg: 'Бот отключился' });
  exitOnce();
});

bot.on('error', err => {
  send({ type: 'error', msg: err.message });
  exitOnce();
});

// -------------------- Чтение команд Python --------------------
const rl = readline.createInterface({ input: process.stdin });

rl.on('line', line => {
  if (!line) return;
  try {
    const cmd = JSON.parse(line);

    if (cmd.action === 'chat' && cmd.text)
      bot.chat(cmd.text);

    if (cmd.action === 'quit') {
      bot.quit("Выход по команде Python");
      setTimeout(exitOnce, 300);
    }


  } catch (e) {
    send({ type: 'error', msg: '[STDIN ERROR] ' + e.message });
  }
});

"""

EventHandler = Callable[..., None]

class MinecraftBot:
    def __init__(
        self,
        node_path: str,
        bot_js_path: str,
        host: str,
        username: str,
        version: str,
        port: Optional[int] = None,
    ):
        self.node_path = node_path
        self.bot_js_path = bot_js_path
        self.host = host
        self.port = port
        self.username = username
        self.version = version

        self.process: Optional[subprocess.Popen] = None
        self.handlers: Dict[str, EventHandler] = {}

        self._prepare_bot_js()

    def _prepare_bot_js(self):
        os.makedirs(os.path.dirname(self.bot_js_path) or ".", exist_ok=True)
        if not os.path.exists(self.bot_js_path):
            with open(self.bot_js_path, "w", encoding="utf-8") as f:
                f.write(NODE_JS_CODE)

    def start(self):
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
            encoding="utf-8",  # важно для кириллицы
            errors="replace",
        )

        threading.Thread(target=self._reader, daemon=True).start()

    def stop(self):
        if self.process and self.process.poll() is None:
            self._send({"action": "quit"})
            time.sleep(0.3)
            self.process.kill()

    def chat(self, text: str):
        self._send({"action": "chat", "text": text})

    def follow(self, player: str):
        self._send({"action": "follow", "player": player})

    def stop_follow(self):
        self._send({"action": "stopFollow"})

    def on(self, event: str, handler: EventHandler):
        """Регистрация обработчика событий"""
        self.handlers[event] = handler

    def _send(self, data: dict):
        if not self.process or self.process.poll() is not None:
            return
        try:
            self.process.stdin.write(json.dumps(data) + "\n")
            self.process.stdin.flush()
        except Exception:
            pass

    def _reader(self):
        assert self.process and self.process.stdout
        for line in self.process.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_type = event.get("type")
            handler = self.handlers.get(event_type)
            if handler:
                try:
                    handler(**{k: v for k, v in event.items() if k != "type"})
                except Exception:
                    pass
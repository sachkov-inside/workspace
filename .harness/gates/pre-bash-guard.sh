#!/usr/bin/env bash
# Блокирует команды, которые проект объявил запрещёнными.
#
# Списков два, и разделение принципиально:
#   .harness/deny-commands.txt        пакетный, generated, приходит с обновлением
#   .harness/deny-commands.local.txt  проектный, пакет его не трогает никогда
#
# Раньше файл был один, и проекту предлагалось дописывать свой блок в его конец. Так
# education-platform и сделал, после чего файл навсегда стал «осознанно расходящимся»:
# `harness update` не имеет права затирать локальные правки, поэтому новые запреты пакета
# до проекта больше не доходили. Хуже всего, что `diff` при этом показывал «совпадает с
# пакетом»: проект выглядел обновлённым и молча терял правила.
#
# Формат в обоих: одна расширенная регулярка на строку, пустые строки и `#` игнорируются.
# Текстовый специально: правило добавляется правкой файла, а не правкой скрипта.
#
# Контракт: JSON со stdin, причина в stderr, exit 2 отменяет вызов.
#
# Решение владельца 2026-08-07: гейт на работу с ветками (primary checkout, protected
# branches, `git switch`/`git checkout`) удалён вместе с pre-worktree-guard.py. Дисциплина
# «в какой ветке вести работу» держится в скиллах и командах владельца, а не в гейтах.
# Здесь остаётся только deny-список опасных команд.

set -u

input=$(cat)
cmd=$(printf '%s' "$input" | python3 -c \
	"import json,sys;print((json.load(sys.stdin).get('tool_input') or {}).get('command',''))" 2>/dev/null)
[ -z "$cmd" ] && exit 0

cwd=$(printf '%s' "$input" | python3 -c \
	"import json,sys;print(json.load(sys.stdin).get('cwd',''))" 2>/dev/null)
[ -z "$cwd" ] && cwd="${CLAUDE_PROJECT_DIR:-$PWD}"
repo=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null) || repo="$cwd"

for deny in "$repo/.harness/deny-commands.txt" "$repo/.harness/deny-commands.local.txt"; do
	[ -f "$deny" ] || continue
	while IFS= read -r line || [ -n "$line" ]; do
		case "$line" in '' | '#'*) continue ;; esac
		pattern="${line%%|##|*}"
		reason="${line#*|##|}"
		[ "$reason" = "$line" ] && reason="команда запрещена правилами проекта"
		if printf '%s' "$cmd" | grep -Eq -- "$pattern" 2>/dev/null; then
			{
				echo "PRE-BASH-ГЕЙТ: $reason"
				echo "  команда: $cmd"
				echo "  правило: $pattern ($(basename "$deny"))"
			} >&2
			exit 2
		fi
	done <"$deny"
done

exit 0

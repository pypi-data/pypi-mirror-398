var __create = Object.create;
var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __getOwnPropNames = Object.getOwnPropertyNames;
var __getProtoOf = Object.getPrototypeOf;
var __hasOwnProp = Object.prototype.hasOwnProperty;
var __commonJS = (cb, mod) => function __require() {
  return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
};
var __export = (target, all2) => {
  for (var name2 in all2)
    __defProp(target, name2, { get: all2[name2], enumerable: true });
};
var __copyProps = (to, from, except, desc) => {
  if (from && typeof from === "object" || typeof from === "function") {
    for (let key of __getOwnPropNames(from))
      if (!__hasOwnProp.call(to, key) && key !== except)
        __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
  }
  return to;
};
var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
  // If the importer is in node compatibility mode or this is not an ESM
  // file that has been converted to a CommonJS file using a Babel-
  // compatible transform (i.e. "__esModule" has not been set), then set
  // "default" to the CommonJS "module.exports" for node compatibility.
  isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
  mod
));
var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

// node_modules/is-buffer/index.js
var require_is_buffer = __commonJS({
  "node_modules/is-buffer/index.js"(exports2, module2) {
    module2.exports = function isBuffer(obj) {
      return obj != null && obj.constructor != null && typeof obj.constructor.isBuffer === "function" && obj.constructor.isBuffer(obj);
    };
  }
});

// node_modules/nspell/lib/util/rule-codes.js
var require_rule_codes = __commonJS({
  "node_modules/nspell/lib/util/rule-codes.js"(exports2, module2) {
    "use strict";
    module2.exports = ruleCodes;
    var NO_CODES = [];
    function ruleCodes(flags, value) {
      var index = 0;
      var result;
      if (!value) return NO_CODES;
      if (flags.FLAG === "long") {
        result = new Array(Math.ceil(value.length / 2));
        while (index < value.length) {
          result[index / 2] = value.slice(index, index + 2);
          index += 2;
        }
        return result;
      }
      return value.split(flags.FLAG === "num" ? "," : "");
    }
  }
});

// node_modules/nspell/lib/util/affix.js
var require_affix = __commonJS({
  "node_modules/nspell/lib/util/affix.js"(exports2, module2) {
    "use strict";
    var parse = require_rule_codes();
    module2.exports = affix;
    var push = [].push;
    var alphabet = "etaoinshrdlcumwfgypbvkjxqz".split("");
    var whiteSpaceExpression = /\s+/;
    var defaultKeyboardLayout = [
      "qwertzuop",
      "yxcvbnm",
      "qaw",
      "say",
      "wse",
      "dsx",
      "sy",
      "edr",
      "fdc",
      "dx",
      "rft",
      "gfv",
      "fc",
      "tgz",
      "hgb",
      "gv",
      "zhu",
      "jhn",
      "hb",
      "uji",
      "kjm",
      "jn",
      "iko",
      "lkm"
    ];
    function affix(doc) {
      var rules = /* @__PURE__ */ Object.create(null);
      var compoundRuleCodes = /* @__PURE__ */ Object.create(null);
      var flags = /* @__PURE__ */ Object.create(null);
      var replacementTable = [];
      var conversion = { in: [], out: [] };
      var compoundRules = [];
      var aff = doc.toString("utf8");
      var lines = [];
      var last = 0;
      var index = aff.indexOf("\n");
      var parts;
      var line;
      var ruleType;
      var count;
      var remove;
      var add;
      var source;
      var entry;
      var position;
      var rule;
      var value;
      var offset;
      var character;
      flags.KEY = [];
      while (index > -1) {
        pushLine(aff.slice(last, index));
        last = index + 1;
        index = aff.indexOf("\n", last);
      }
      pushLine(aff.slice(last));
      index = -1;
      while (++index < lines.length) {
        line = lines[index];
        parts = line.split(whiteSpaceExpression);
        ruleType = parts[0];
        if (ruleType === "REP") {
          count = index + parseInt(parts[1], 10);
          while (++index <= count) {
            parts = lines[index].split(whiteSpaceExpression);
            replacementTable.push([parts[1], parts[2]]);
          }
          index--;
        } else if (ruleType === "ICONV" || ruleType === "OCONV") {
          count = index + parseInt(parts[1], 10);
          entry = conversion[ruleType === "ICONV" ? "in" : "out"];
          while (++index <= count) {
            parts = lines[index].split(whiteSpaceExpression);
            entry.push([new RegExp(parts[1], "g"), parts[2]]);
          }
          index--;
        } else if (ruleType === "COMPOUNDRULE") {
          count = index + parseInt(parts[1], 10);
          while (++index <= count) {
            rule = lines[index].split(whiteSpaceExpression)[1];
            position = -1;
            compoundRules.push(rule);
            while (++position < rule.length) {
              compoundRuleCodes[rule.charAt(position)] = [];
            }
          }
          index--;
        } else if (ruleType === "PFX" || ruleType === "SFX") {
          count = index + parseInt(parts[3], 10);
          rule = {
            type: ruleType,
            combineable: parts[2] === "Y",
            entries: []
          };
          rules[parts[1]] = rule;
          while (++index <= count) {
            parts = lines[index].split(whiteSpaceExpression);
            remove = parts[2];
            add = parts[3].split("/");
            source = parts[4];
            entry = {
              add: "",
              remove: "",
              match: "",
              continuation: parse(flags, add[1])
            };
            if (add && add[0] !== "0") {
              entry.add = add[0];
            }
            try {
              if (remove !== "0") {
                entry.remove = ruleType === "SFX" ? end(remove) : remove;
              }
              if (source && source !== ".") {
                entry.match = ruleType === "SFX" ? end(source) : start(source);
              }
            } catch (_) {
              entry = null;
            }
            if (entry) {
              rule.entries.push(entry);
            }
          }
          index--;
        } else if (ruleType === "TRY") {
          source = parts[1];
          offset = -1;
          value = [];
          while (++offset < source.length) {
            character = source.charAt(offset);
            if (character.toLowerCase() === character) {
              value.push(character);
            }
          }
          offset = -1;
          while (++offset < alphabet.length) {
            if (source.indexOf(alphabet[offset]) < 0) {
              value.push(alphabet[offset]);
            }
          }
          flags[ruleType] = value;
        } else if (ruleType === "KEY") {
          push.apply(flags[ruleType], parts[1].split("|"));
        } else if (ruleType === "COMPOUNDMIN") {
          flags[ruleType] = Number(parts[1]);
        } else if (ruleType === "ONLYINCOMPOUND") {
          flags[ruleType] = parts[1];
          compoundRuleCodes[parts[1]] = [];
        } else if (ruleType === "FLAG" || ruleType === "KEEPCASE" || ruleType === "NOSUGGEST" || ruleType === "WORDCHARS") {
          flags[ruleType] = parts[1];
        } else {
          flags[ruleType] = parts[1];
        }
      }
      if (isNaN(flags.COMPOUNDMIN)) {
        flags.COMPOUNDMIN = 3;
      }
      if (!flags.KEY.length) {
        flags.KEY = defaultKeyboardLayout;
      }
      if (!flags.TRY) {
        flags.TRY = alphabet.concat();
      }
      if (!flags.KEEPCASE) {
        flags.KEEPCASE = false;
      }
      return {
        compoundRuleCodes,
        replacementTable,
        conversion,
        compoundRules,
        rules,
        flags
      };
      function pushLine(line2) {
        line2 = line2.trim();
        if (line2 && line2.charCodeAt(0) !== 35) {
          lines.push(line2);
        }
      }
    }
    function end(source) {
      return new RegExp(source + "$");
    }
    function start(source) {
      return new RegExp("^" + source);
    }
  }
});

// node_modules/nspell/lib/util/normalize.js
var require_normalize = __commonJS({
  "node_modules/nspell/lib/util/normalize.js"(exports2, module2) {
    "use strict";
    module2.exports = normalize;
    function normalize(value, patterns) {
      var index = -1;
      while (++index < patterns.length) {
        value = value.replace(patterns[index][0], patterns[index][1]);
      }
      return value;
    }
  }
});

// node_modules/nspell/lib/util/flag.js
var require_flag = __commonJS({
  "node_modules/nspell/lib/util/flag.js"(exports2, module2) {
    "use strict";
    module2.exports = flag;
    function flag(values, value, flags) {
      return flags && value in values && flags.indexOf(values[value]) > -1;
    }
  }
});

// node_modules/nspell/lib/util/exact.js
var require_exact = __commonJS({
  "node_modules/nspell/lib/util/exact.js"(exports2, module2) {
    "use strict";
    var flag = require_flag();
    module2.exports = exact;
    function exact(context, value) {
      var index = -1;
      if (context.data[value]) {
        return !flag(context.flags, "ONLYINCOMPOUND", context.data[value]);
      }
      if (value.length >= context.flags.COMPOUNDMIN) {
        while (++index < context.compoundRules.length) {
          if (context.compoundRules[index].test(value)) {
            return true;
          }
        }
      }
      return false;
    }
  }
});

// node_modules/nspell/lib/util/form.js
var require_form = __commonJS({
  "node_modules/nspell/lib/util/form.js"(exports2, module2) {
    "use strict";
    var normalize = require_normalize();
    var exact = require_exact();
    var flag = require_flag();
    module2.exports = form;
    function form(context, value, all2) {
      var normal = value.trim();
      var alternative;
      if (!normal) {
        return null;
      }
      normal = normalize(normal, context.conversion.in);
      if (exact(context, normal)) {
        if (!all2 && flag(context.flags, "FORBIDDENWORD", context.data[normal])) {
          return null;
        }
        return normal;
      }
      if (normal.toUpperCase() === normal) {
        alternative = normal.charAt(0) + normal.slice(1).toLowerCase();
        if (ignore(context.flags, context.data[alternative], all2)) {
          return null;
        }
        if (exact(context, alternative)) {
          return alternative;
        }
      }
      alternative = normal.toLowerCase();
      if (alternative !== normal) {
        if (ignore(context.flags, context.data[alternative], all2)) {
          return null;
        }
        if (exact(context, alternative)) {
          return alternative;
        }
      }
      return null;
    }
    function ignore(flags, dict, all2) {
      return flag(flags, "KEEPCASE", dict) || all2 || flag(flags, "FORBIDDENWORD", dict);
    }
  }
});

// node_modules/nspell/lib/correct.js
var require_correct = __commonJS({
  "node_modules/nspell/lib/correct.js"(exports2, module2) {
    "use strict";
    var form = require_form();
    module2.exports = correct;
    function correct(value) {
      return Boolean(form(this, value));
    }
  }
});

// node_modules/nspell/lib/util/casing.js
var require_casing = __commonJS({
  "node_modules/nspell/lib/util/casing.js"(exports2, module2) {
    "use strict";
    module2.exports = casing;
    function casing(value) {
      var head = exact(value.charAt(0));
      var rest = value.slice(1);
      if (!rest) {
        return head;
      }
      rest = exact(rest);
      if (head === rest) {
        return head;
      }
      if (head === "u" && rest === "l") {
        return "s";
      }
      return null;
    }
    function exact(value) {
      return value === value.toLowerCase() ? "l" : value === value.toUpperCase() ? "u" : null;
    }
  }
});

// node_modules/nspell/lib/suggest.js
var require_suggest = __commonJS({
  "node_modules/nspell/lib/suggest.js"(exports2, module2) {
    "use strict";
    var casing = require_casing();
    var normalize = require_normalize();
    var flag = require_flag();
    var form = require_form();
    module2.exports = suggest;
    var push = [].push;
    function suggest(value) {
      var self2 = this;
      var charAdded = {};
      var suggestions = [];
      var weighted = {};
      var memory;
      var replacement;
      var edits = [];
      var values;
      var index;
      var offset;
      var position;
      var count;
      var otherOffset;
      var otherCharacter;
      var character;
      var group;
      var before;
      var after;
      var upper;
      var insensitive;
      var firstLevel;
      var previous;
      var next;
      var nextCharacter;
      var max;
      var distance;
      var size;
      var normalized;
      var suggestion;
      var currentCase;
      value = normalize(value.trim(), self2.conversion.in);
      if (!value || self2.correct(value)) {
        return [];
      }
      currentCase = casing(value);
      index = -1;
      while (++index < self2.replacementTable.length) {
        replacement = self2.replacementTable[index];
        offset = value.indexOf(replacement[0]);
        while (offset > -1) {
          edits.push(value.replace(replacement[0], replacement[1]));
          offset = value.indexOf(replacement[0], offset + 1);
        }
      }
      index = -1;
      while (++index < value.length) {
        character = value.charAt(index);
        before = value.slice(0, index);
        after = value.slice(index + 1);
        insensitive = character.toLowerCase();
        upper = insensitive !== character;
        charAdded = {};
        offset = -1;
        while (++offset < self2.flags.KEY.length) {
          group = self2.flags.KEY[offset];
          position = group.indexOf(insensitive);
          if (position < 0) {
            continue;
          }
          otherOffset = -1;
          while (++otherOffset < group.length) {
            if (otherOffset !== position) {
              otherCharacter = group.charAt(otherOffset);
              if (charAdded[otherCharacter]) {
                continue;
              }
              charAdded[otherCharacter] = true;
              if (upper) {
                otherCharacter = otherCharacter.toUpperCase();
              }
              edits.push(before + otherCharacter + after);
            }
          }
        }
      }
      index = -1;
      nextCharacter = value.charAt(0);
      values = [""];
      max = 1;
      distance = 0;
      while (++index < value.length) {
        character = nextCharacter;
        nextCharacter = value.charAt(index + 1);
        before = value.slice(0, index);
        replacement = character === nextCharacter ? "" : character + character;
        offset = -1;
        count = values.length;
        while (++offset < count) {
          if (offset <= max) {
            values.push(values[offset] + replacement);
          }
          values[offset] += character;
        }
        if (++distance < 3) {
          max = values.length;
        }
      }
      push.apply(edits, values);
      values = [value];
      replacement = value.toLowerCase();
      if (value === replacement || currentCase === null) {
        values.push(value.charAt(0).toUpperCase() + replacement.slice(1));
      }
      replacement = value.toUpperCase();
      if (value !== replacement) {
        values.push(replacement);
      }
      memory = {
        state: {},
        weighted,
        suggestions
      };
      firstLevel = generate(self2, memory, values, edits);
      previous = 0;
      max = Math.min(firstLevel.length, Math.pow(Math.max(15 - value.length, 3), 3));
      size = Math.max(Math.pow(10 - value.length, 3), 1);
      while (!suggestions.length && previous < max) {
        next = previous + size;
        generate(self2, memory, firstLevel.slice(previous, next));
        previous = next;
      }
      suggestions.sort(sort);
      values = [];
      normalized = [];
      index = -1;
      while (++index < suggestions.length) {
        suggestion = normalize(suggestions[index], self2.conversion.out);
        replacement = suggestion.toLowerCase();
        if (normalized.indexOf(replacement) < 0) {
          values.push(suggestion);
          normalized.push(replacement);
        }
      }
      return values;
      function sort(a, b) {
        return sortWeight(a, b) || sortCasing(a, b) || sortAlpha(a, b);
      }
      function sortWeight(a, b) {
        return weighted[a] === weighted[b] ? 0 : weighted[a] > weighted[b] ? -1 : 1;
      }
      function sortCasing(a, b) {
        var leftCasing = casing(a);
        var rightCasing = casing(b);
        return leftCasing === rightCasing ? 0 : leftCasing === currentCase ? -1 : rightCasing === currentCase ? 1 : void 0;
      }
      function sortAlpha(a, b) {
        return a.localeCompare(b);
      }
    }
    function generate(context, memory, words, edits) {
      var characters = context.flags.TRY;
      var data = context.data;
      var flags = context.flags;
      var result = [];
      var index = -1;
      var word;
      var before;
      var character;
      var nextCharacter;
      var nextAfter;
      var nextNextAfter;
      var nextUpper;
      var currentCase;
      var position;
      var after;
      var upper;
      var inject;
      var offset;
      if (edits) {
        while (++index < edits.length) {
          check(edits[index], true);
        }
      }
      index = -1;
      while (++index < words.length) {
        word = words[index];
        before = "";
        character = "";
        nextCharacter = word.charAt(0);
        nextAfter = word;
        nextNextAfter = word.slice(1);
        nextUpper = nextCharacter.toLowerCase() !== nextCharacter;
        currentCase = casing(word);
        position = -1;
        while (++position <= word.length) {
          before += character;
          after = nextAfter;
          nextAfter = nextNextAfter;
          nextNextAfter = nextAfter.slice(1);
          character = nextCharacter;
          nextCharacter = word.charAt(position + 1);
          upper = nextUpper;
          if (nextCharacter) {
            nextUpper = nextCharacter.toLowerCase() !== nextCharacter;
          }
          if (nextAfter && upper !== nextUpper) {
            check(before + switchCase(nextAfter));
            check(
              before + switchCase(nextCharacter) + switchCase(character) + nextNextAfter
            );
          }
          check(before + nextAfter);
          if (nextAfter) {
            check(before + nextCharacter + character + nextNextAfter);
          }
          offset = -1;
          while (++offset < characters.length) {
            inject = characters[offset];
            if (upper && inject !== inject.toUpperCase()) {
              if (currentCase !== "s") {
                check(before + inject + after);
                check(before + inject + nextAfter);
              }
              inject = inject.toUpperCase();
              check(before + inject + after);
              check(before + inject + nextAfter);
            } else {
              check(before + inject + after);
              check(before + inject + nextAfter);
            }
          }
        }
      }
      return result;
      function check(value, double) {
        var state = memory.state[value];
        var corrected;
        if (state !== Boolean(state)) {
          result.push(value);
          corrected = form(context, value);
          state = corrected && !flag(flags, "NOSUGGEST", data[corrected]);
          memory.state[value] = state;
          if (state) {
            memory.weighted[value] = double ? 10 : 0;
            memory.suggestions.push(value);
          }
        }
        if (state) {
          memory.weighted[value]++;
        }
      }
      function switchCase(fragment) {
        var first = fragment.charAt(0);
        return (first.toLowerCase() === first ? first.toUpperCase() : first.toLowerCase()) + fragment.slice(1);
      }
    }
  }
});

// node_modules/nspell/lib/spell.js
var require_spell = __commonJS({
  "node_modules/nspell/lib/spell.js"(exports2, module2) {
    "use strict";
    var form = require_form();
    var flag = require_flag();
    module2.exports = spell;
    function spell(word) {
      var self2 = this;
      var value = form(self2, word, true);
      return {
        correct: self2.correct(word),
        forbidden: Boolean(
          value && flag(self2.flags, "FORBIDDENWORD", self2.data[value])
        ),
        warn: Boolean(value && flag(self2.flags, "WARN", self2.data[value]))
      };
    }
  }
});

// node_modules/nspell/lib/util/apply.js
var require_apply = __commonJS({
  "node_modules/nspell/lib/util/apply.js"(exports2, module2) {
    "use strict";
    module2.exports = apply;
    function apply(value, rule, rules, words) {
      var index = -1;
      var entry;
      var next;
      var continuationRule;
      var continuation;
      var position;
      while (++index < rule.entries.length) {
        entry = rule.entries[index];
        continuation = entry.continuation;
        position = -1;
        if (!entry.match || entry.match.test(value)) {
          next = entry.remove ? value.replace(entry.remove, "") : value;
          next = rule.type === "SFX" ? next + entry.add : entry.add + next;
          words.push(next);
          if (continuation && continuation.length) {
            while (++position < continuation.length) {
              continuationRule = rules[continuation[position]];
              if (continuationRule) {
                apply(next, continuationRule, rules, words);
              }
            }
          }
        }
      }
      return words;
    }
  }
});

// node_modules/nspell/lib/util/add.js
var require_add = __commonJS({
  "node_modules/nspell/lib/util/add.js"(exports2, module2) {
    "use strict";
    var apply = require_apply();
    module2.exports = add;
    var push = [].push;
    var NO_RULES = [];
    function addRules(dict, word, rules) {
      var curr = dict[word];
      if (word in dict) {
        if (curr === NO_RULES) {
          dict[word] = rules.concat();
        } else {
          push.apply(curr, rules);
        }
      } else {
        dict[word] = rules.concat();
      }
    }
    function add(dict, word, codes, options) {
      var position = -1;
      var rule;
      var offset;
      var subposition;
      var suboffset;
      var combined;
      var newWords;
      var otherNewWords;
      if (!("NEEDAFFIX" in options.flags) || codes.indexOf(options.flags.NEEDAFFIX) < 0) {
        addRules(dict, word, codes);
      }
      while (++position < codes.length) {
        rule = options.rules[codes[position]];
        if (codes[position] in options.compoundRuleCodes) {
          options.compoundRuleCodes[codes[position]].push(word);
        }
        if (rule) {
          newWords = apply(word, rule, options.rules, []);
          offset = -1;
          while (++offset < newWords.length) {
            if (!(newWords[offset] in dict)) {
              dict[newWords[offset]] = NO_RULES;
            }
            if (rule.combineable) {
              subposition = position;
              while (++subposition < codes.length) {
                combined = options.rules[codes[subposition]];
                if (combined && combined.combineable && rule.type !== combined.type) {
                  otherNewWords = apply(
                    newWords[offset],
                    combined,
                    options.rules,
                    []
                  );
                  suboffset = -1;
                  while (++suboffset < otherNewWords.length) {
                    if (!(otherNewWords[suboffset] in dict)) {
                      dict[otherNewWords[suboffset]] = NO_RULES;
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
});

// node_modules/nspell/lib/add.js
var require_add2 = __commonJS({
  "node_modules/nspell/lib/add.js"(exports2, module2) {
    "use strict";
    var push = require_add();
    module2.exports = add;
    var NO_CODES = [];
    function add(value, model) {
      var self2 = this;
      push(self2.data, value, self2.data[model] || NO_CODES, self2);
      return self2;
    }
  }
});

// node_modules/nspell/lib/remove.js
var require_remove = __commonJS({
  "node_modules/nspell/lib/remove.js"(exports2, module2) {
    "use strict";
    module2.exports = remove;
    function remove(value) {
      var self2 = this;
      delete self2.data[value];
      return self2;
    }
  }
});

// node_modules/nspell/lib/word-characters.js
var require_word_characters = __commonJS({
  "node_modules/nspell/lib/word-characters.js"(exports2, module2) {
    "use strict";
    module2.exports = wordCharacters;
    function wordCharacters() {
      return this.flags.WORDCHARS || null;
    }
  }
});

// node_modules/nspell/lib/util/dictionary.js
var require_dictionary = __commonJS({
  "node_modules/nspell/lib/util/dictionary.js"(exports2, module2) {
    "use strict";
    var parseCodes = require_rule_codes();
    var add = require_add();
    module2.exports = parse;
    var whiteSpaceExpression = /\s/g;
    function parse(buf, options, dict) {
      var value = buf.toString("utf8");
      var last = value.indexOf("\n") + 1;
      var index = value.indexOf("\n", last);
      while (index > -1) {
        if (value.charCodeAt(last) !== 9) {
          parseLine(value.slice(last, index), options, dict);
        }
        last = index + 1;
        index = value.indexOf("\n", last);
      }
      parseLine(value.slice(last), options, dict);
    }
    function parseLine(line, options, dict) {
      var slashOffset = line.indexOf("/");
      var hashOffset = line.indexOf("#");
      var codes = "";
      var word;
      var result;
      while (slashOffset > -1 && line.charCodeAt(slashOffset - 1) === 92) {
        line = line.slice(0, slashOffset - 1) + line.slice(slashOffset);
        slashOffset = line.indexOf("/", slashOffset);
      }
      if (hashOffset > -1) {
        if (slashOffset > -1 && slashOffset < hashOffset) {
          word = line.slice(0, slashOffset);
          whiteSpaceExpression.lastIndex = slashOffset + 1;
          result = whiteSpaceExpression.exec(line);
          codes = line.slice(slashOffset + 1, result ? result.index : void 0);
        } else {
          word = line.slice(0, hashOffset);
        }
      } else if (slashOffset > -1) {
        word = line.slice(0, slashOffset);
        codes = line.slice(slashOffset + 1);
      } else {
        word = line;
      }
      word = word.trim();
      if (word) {
        add(dict, word, parseCodes(options.flags, codes.trim()), options);
      }
    }
  }
});

// node_modules/nspell/lib/dictionary.js
var require_dictionary2 = __commonJS({
  "node_modules/nspell/lib/dictionary.js"(exports2, module2) {
    "use strict";
    var parse = require_dictionary();
    module2.exports = add;
    function add(buf) {
      var self2 = this;
      var index = -1;
      var rule;
      var source;
      var character;
      var offset;
      parse(buf, self2, self2.data);
      while (++index < self2.compoundRules.length) {
        rule = self2.compoundRules[index];
        source = "";
        offset = -1;
        while (++offset < rule.length) {
          character = rule.charAt(offset);
          source += self2.compoundRuleCodes[character].length ? "(?:" + self2.compoundRuleCodes[character].join("|") + ")" : character;
        }
        self2.compoundRules[index] = new RegExp(source, "i");
      }
      return self2;
    }
  }
});

// node_modules/nspell/lib/personal.js
var require_personal = __commonJS({
  "node_modules/nspell/lib/personal.js"(exports2, module2) {
    "use strict";
    module2.exports = add;
    function add(buf) {
      var self2 = this;
      var lines = buf.toString("utf8").split("\n");
      var index = -1;
      var line;
      var forbidden;
      var word;
      var flag;
      if (self2.flags.FORBIDDENWORD === void 0) self2.flags.FORBIDDENWORD = false;
      flag = self2.flags.FORBIDDENWORD;
      while (++index < lines.length) {
        line = lines[index].trim();
        if (!line) {
          continue;
        }
        line = line.split("/");
        word = line[0];
        forbidden = word.charAt(0) === "*";
        if (forbidden) {
          word = word.slice(1);
        }
        self2.add(word, line[1]);
        if (forbidden) {
          self2.data[word].push(flag);
        }
      }
      return self2;
    }
  }
});

// node_modules/nspell/lib/index.js
var require_lib = __commonJS({
  "node_modules/nspell/lib/index.js"(exports2, module2) {
    "use strict";
    var buffer = require_is_buffer();
    var affix = require_affix();
    module2.exports = NSpell;
    var proto = NSpell.prototype;
    proto.correct = require_correct();
    proto.suggest = require_suggest();
    proto.spell = require_spell();
    proto.add = require_add2();
    proto.remove = require_remove();
    proto.wordCharacters = require_word_characters();
    proto.dictionary = require_dictionary2();
    proto.personal = require_personal();
    function NSpell(aff, dic) {
      var index = -1;
      var dictionaries;
      if (!(this instanceof NSpell)) {
        return new NSpell(aff, dic);
      }
      if (typeof aff === "string" || buffer(aff)) {
        if (typeof dic === "string" || buffer(dic)) {
          dictionaries = [{ dic }];
        }
      } else if (aff) {
        if ("length" in aff) {
          dictionaries = aff;
          aff = aff[0] && aff[0].aff;
        } else {
          if (aff.dic) {
            dictionaries = [aff];
          }
          aff = aff.aff;
        }
      }
      if (!aff) {
        throw new Error("Missing `aff` in dictionary");
      }
      aff = affix(aff);
      this.data = /* @__PURE__ */ Object.create(null);
      this.compoundRuleCodes = aff.compoundRuleCodes;
      this.replacementTable = aff.replacementTable;
      this.conversion = aff.conversion;
      this.compoundRules = aff.compoundRules;
      this.rules = aff.rules;
      this.flags = aff.flags;
      if (dictionaries) {
        while (++index < dictionaries.length) {
          if (dictionaries[index].dic) {
            this.dictionary(dictionaries[index].dic);
          }
        }
      }
    }
  }
});

// node_modules/es5-ext/function/noop.js
var require_noop = __commonJS({
  "node_modules/es5-ext/function/noop.js"(exports2, module2) {
    "use strict";
    module2.exports = function() {
    };
  }
});

// node_modules/es5-ext/object/is-value.js
var require_is_value = __commonJS({
  "node_modules/es5-ext/object/is-value.js"(exports2, module2) {
    "use strict";
    var _undefined = require_noop()();
    module2.exports = function(val) {
      return val !== _undefined && val !== null;
    };
  }
});

// node_modules/es5-ext/object/normalize-options.js
var require_normalize_options = __commonJS({
  "node_modules/es5-ext/object/normalize-options.js"(exports2, module2) {
    "use strict";
    var isValue = require_is_value();
    var forEach = Array.prototype.forEach;
    var create = Object.create;
    var process2 = function(src, obj) {
      var key;
      for (key in src) obj[key] = src[key];
    };
    module2.exports = function(opts1) {
      var result = create(null);
      forEach.call(arguments, function(options) {
        if (!isValue(options)) return;
        process2(Object(options), result);
      });
      return result;
    };
  }
});

// node_modules/es5-ext/math/sign/is-implemented.js
var require_is_implemented = __commonJS({
  "node_modules/es5-ext/math/sign/is-implemented.js"(exports2, module2) {
    "use strict";
    module2.exports = function() {
      var sign = Math.sign;
      if (typeof sign !== "function") return false;
      return sign(10) === 1 && sign(-20) === -1;
    };
  }
});

// node_modules/es5-ext/math/sign/shim.js
var require_shim = __commonJS({
  "node_modules/es5-ext/math/sign/shim.js"(exports2, module2) {
    "use strict";
    module2.exports = function(value) {
      value = Number(value);
      if (isNaN(value) || value === 0) return value;
      return value > 0 ? 1 : -1;
    };
  }
});

// node_modules/es5-ext/math/sign/index.js
var require_sign = __commonJS({
  "node_modules/es5-ext/math/sign/index.js"(exports2, module2) {
    "use strict";
    module2.exports = require_is_implemented()() ? Math.sign : require_shim();
  }
});

// node_modules/es5-ext/number/to-integer.js
var require_to_integer = __commonJS({
  "node_modules/es5-ext/number/to-integer.js"(exports2, module2) {
    "use strict";
    var sign = require_sign();
    var abs = Math.abs;
    var floor = Math.floor;
    module2.exports = function(value) {
      if (isNaN(value)) return 0;
      value = Number(value);
      if (value === 0 || !isFinite(value)) return value;
      return sign(value) * floor(abs(value));
    };
  }
});

// node_modules/es5-ext/number/to-pos-integer.js
var require_to_pos_integer = __commonJS({
  "node_modules/es5-ext/number/to-pos-integer.js"(exports2, module2) {
    "use strict";
    var toInteger = require_to_integer();
    var max = Math.max;
    module2.exports = function(value) {
      return max(0, toInteger(value));
    };
  }
});

// node_modules/memoizee/lib/resolve-length.js
var require_resolve_length = __commonJS({
  "node_modules/memoizee/lib/resolve-length.js"(exports2, module2) {
    "use strict";
    var toPosInt = require_to_pos_integer();
    module2.exports = function(optsLength, fnLength, isAsync) {
      var length;
      if (isNaN(optsLength)) {
        length = fnLength;
        if (!(length >= 0)) return 1;
        if (isAsync && length) return length - 1;
        return length;
      }
      if (optsLength === false) return false;
      return toPosInt(optsLength);
    };
  }
});

// node_modules/es5-ext/object/valid-callable.js
var require_valid_callable = __commonJS({
  "node_modules/es5-ext/object/valid-callable.js"(exports2, module2) {
    "use strict";
    module2.exports = function(fn) {
      if (typeof fn !== "function") throw new TypeError(fn + " is not a function");
      return fn;
    };
  }
});

// node_modules/es5-ext/object/valid-value.js
var require_valid_value = __commonJS({
  "node_modules/es5-ext/object/valid-value.js"(exports2, module2) {
    "use strict";
    var isValue = require_is_value();
    module2.exports = function(value) {
      if (!isValue(value)) throw new TypeError("Cannot use null or undefined");
      return value;
    };
  }
});

// node_modules/es5-ext/object/_iterate.js
var require_iterate = __commonJS({
  "node_modules/es5-ext/object/_iterate.js"(exports2, module2) {
    "use strict";
    var callable = require_valid_callable();
    var value = require_valid_value();
    var bind = Function.prototype.bind;
    var call = Function.prototype.call;
    var keys = Object.keys;
    var objPropertyIsEnumerable = Object.prototype.propertyIsEnumerable;
    module2.exports = function(method, defVal) {
      return function(obj, cb) {
        var list, thisArg = arguments[2], compareFn = arguments[3];
        obj = Object(value(obj));
        callable(cb);
        list = keys(obj);
        if (compareFn) {
          list.sort(typeof compareFn === "function" ? bind.call(compareFn, obj) : void 0);
        }
        if (typeof method !== "function") method = list[method];
        return call.call(method, list, function(key, index) {
          if (!objPropertyIsEnumerable.call(obj, key)) return defVal;
          return call.call(cb, thisArg, obj[key], key, obj, index);
        });
      };
    };
  }
});

// node_modules/es5-ext/object/for-each.js
var require_for_each = __commonJS({
  "node_modules/es5-ext/object/for-each.js"(exports2, module2) {
    "use strict";
    module2.exports = require_iterate()("forEach");
  }
});

// node_modules/memoizee/lib/registered-extensions.js
var require_registered_extensions = __commonJS({
  "node_modules/memoizee/lib/registered-extensions.js"() {
    "use strict";
  }
});

// node_modules/es5-ext/object/assign/is-implemented.js
var require_is_implemented2 = __commonJS({
  "node_modules/es5-ext/object/assign/is-implemented.js"(exports2, module2) {
    "use strict";
    module2.exports = function() {
      var assign = Object.assign, obj;
      if (typeof assign !== "function") return false;
      obj = { foo: "raz" };
      assign(obj, { bar: "dwa" }, { trzy: "trzy" });
      return obj.foo + obj.bar + obj.trzy === "razdwatrzy";
    };
  }
});

// node_modules/es5-ext/object/keys/is-implemented.js
var require_is_implemented3 = __commonJS({
  "node_modules/es5-ext/object/keys/is-implemented.js"(exports2, module2) {
    "use strict";
    module2.exports = function() {
      try {
        Object.keys("primitive");
        return true;
      } catch (e) {
        return false;
      }
    };
  }
});

// node_modules/es5-ext/object/keys/shim.js
var require_shim2 = __commonJS({
  "node_modules/es5-ext/object/keys/shim.js"(exports2, module2) {
    "use strict";
    var isValue = require_is_value();
    var keys = Object.keys;
    module2.exports = function(object) {
      return keys(isValue(object) ? Object(object) : object);
    };
  }
});

// node_modules/es5-ext/object/keys/index.js
var require_keys = __commonJS({
  "node_modules/es5-ext/object/keys/index.js"(exports2, module2) {
    "use strict";
    module2.exports = require_is_implemented3()() ? Object.keys : require_shim2();
  }
});

// node_modules/es5-ext/object/assign/shim.js
var require_shim3 = __commonJS({
  "node_modules/es5-ext/object/assign/shim.js"(exports2, module2) {
    "use strict";
    var keys = require_keys();
    var value = require_valid_value();
    var max = Math.max;
    module2.exports = function(dest, src) {
      var error, i, length = max(arguments.length, 2), assign;
      dest = Object(value(dest));
      assign = function(key) {
        try {
          dest[key] = src[key];
        } catch (e) {
          if (!error) error = e;
        }
      };
      for (i = 1; i < length; ++i) {
        src = arguments[i];
        keys(src).forEach(assign);
      }
      if (error !== void 0) throw error;
      return dest;
    };
  }
});

// node_modules/es5-ext/object/assign/index.js
var require_assign = __commonJS({
  "node_modules/es5-ext/object/assign/index.js"(exports2, module2) {
    "use strict";
    module2.exports = require_is_implemented2()() ? Object.assign : require_shim3();
  }
});

// node_modules/es5-ext/object/is-object.js
var require_is_object = __commonJS({
  "node_modules/es5-ext/object/is-object.js"(exports2, module2) {
    "use strict";
    var isValue = require_is_value();
    var map = { function: true, object: true };
    module2.exports = function(value) {
      return isValue(value) && map[typeof value] || false;
    };
  }
});

// node_modules/es5-ext/error/custom.js
var require_custom = __commonJS({
  "node_modules/es5-ext/error/custom.js"(exports2, module2) {
    "use strict";
    var assign = require_assign();
    var isObject = require_is_object();
    var isValue = require_is_value();
    var captureStackTrace = Error.captureStackTrace;
    module2.exports = function(message) {
      var err = new Error(message), code = arguments[1], ext = arguments[2];
      if (!isValue(ext)) {
        if (isObject(code)) {
          ext = code;
          code = null;
        }
      }
      if (isValue(ext)) assign(err, ext);
      if (isValue(code)) err.code = code;
      if (captureStackTrace) captureStackTrace(err, module2.exports);
      return err;
    };
  }
});

// node_modules/es5-ext/object/mixin.js
var require_mixin = __commonJS({
  "node_modules/es5-ext/object/mixin.js"(exports2, module2) {
    "use strict";
    var value = require_valid_value();
    var defineProperty = Object.defineProperty;
    var getOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
    var getOwnPropertyNames = Object.getOwnPropertyNames;
    var getOwnPropertySymbols = Object.getOwnPropertySymbols;
    module2.exports = function(target, source) {
      var error, sourceObject = Object(value(source));
      target = Object(value(target));
      getOwnPropertyNames(sourceObject).forEach(function(name2) {
        try {
          defineProperty(target, name2, getOwnPropertyDescriptor(source, name2));
        } catch (e) {
          error = e;
        }
      });
      if (typeof getOwnPropertySymbols === "function") {
        getOwnPropertySymbols(sourceObject).forEach(function(symbol) {
          try {
            defineProperty(target, symbol, getOwnPropertyDescriptor(source, symbol));
          } catch (e) {
            error = e;
          }
        });
      }
      if (error !== void 0) throw error;
      return target;
    };
  }
});

// node_modules/es5-ext/function/_define-length.js
var require_define_length = __commonJS({
  "node_modules/es5-ext/function/_define-length.js"(exports2, module2) {
    "use strict";
    var toPosInt = require_to_pos_integer();
    var test = function(arg1, arg2) {
      return arg2;
    };
    var desc;
    var defineProperty;
    var generate;
    var mixin;
    try {
      Object.defineProperty(test, "length", {
        configurable: true,
        writable: false,
        enumerable: false,
        value: 1
      });
    } catch (ignore) {
    }
    if (test.length === 1) {
      desc = { configurable: true, writable: false, enumerable: false };
      defineProperty = Object.defineProperty;
      module2.exports = function(fn, length) {
        length = toPosInt(length);
        if (fn.length === length) return fn;
        desc.value = length;
        return defineProperty(fn, "length", desc);
      };
    } else {
      mixin = require_mixin();
      generate = /* @__PURE__ */ function() {
        var cache = [];
        return function(length) {
          var args, i = 0;
          if (cache[length]) return cache[length];
          args = [];
          while (length--) args.push("a" + (++i).toString(36));
          return new Function(
            "fn",
            "return function (" + args.join(", ") + ") { return fn.apply(this, arguments); };"
          );
        };
      }();
      module2.exports = function(src, length) {
        var target;
        length = toPosInt(length);
        if (src.length === length) return src;
        target = generate(length)(src);
        try {
          mixin(target, src);
        } catch (ignore) {
        }
        return target;
      };
    }
  }
});

// node_modules/type/value/is.js
var require_is = __commonJS({
  "node_modules/type/value/is.js"(exports2, module2) {
    "use strict";
    var _undefined = void 0;
    module2.exports = function(value) {
      return value !== _undefined && value !== null;
    };
  }
});

// node_modules/type/object/is.js
var require_is2 = __commonJS({
  "node_modules/type/object/is.js"(exports2, module2) {
    "use strict";
    var isValue = require_is();
    var possibleTypes = {
      "object": true,
      "function": true,
      "undefined": true
      /* document.all */
    };
    module2.exports = function(value) {
      if (!isValue(value)) return false;
      return hasOwnProperty.call(possibleTypes, typeof value);
    };
  }
});

// node_modules/type/prototype/is.js
var require_is3 = __commonJS({
  "node_modules/type/prototype/is.js"(exports2, module2) {
    "use strict";
    var isObject = require_is2();
    module2.exports = function(value) {
      if (!isObject(value)) return false;
      try {
        if (!value.constructor) return false;
        return value.constructor.prototype === value;
      } catch (error) {
        return false;
      }
    };
  }
});

// node_modules/type/function/is.js
var require_is4 = __commonJS({
  "node_modules/type/function/is.js"(exports2, module2) {
    "use strict";
    var isPrototype = require_is3();
    module2.exports = function(value) {
      if (typeof value !== "function") return false;
      if (!hasOwnProperty.call(value, "length")) return false;
      try {
        if (typeof value.length !== "number") return false;
        if (typeof value.call !== "function") return false;
        if (typeof value.apply !== "function") return false;
      } catch (error) {
        return false;
      }
      return !isPrototype(value);
    };
  }
});

// node_modules/type/plain-function/is.js
var require_is5 = __commonJS({
  "node_modules/type/plain-function/is.js"(exports2, module2) {
    "use strict";
    var isFunction = require_is4();
    var classRe = /^\s*class[\s{/}]/;
    var functionToString = Function.prototype.toString;
    module2.exports = function(value) {
      if (!isFunction(value)) return false;
      if (classRe.test(functionToString.call(value))) return false;
      return true;
    };
  }
});

// node_modules/es5-ext/string/#/contains/is-implemented.js
var require_is_implemented4 = __commonJS({
  "node_modules/es5-ext/string/#/contains/is-implemented.js"(exports2, module2) {
    "use strict";
    var str = "razdwatrzy";
    module2.exports = function() {
      if (typeof str.contains !== "function") return false;
      return str.contains("dwa") === true && str.contains("foo") === false;
    };
  }
});

// node_modules/es5-ext/string/#/contains/shim.js
var require_shim4 = __commonJS({
  "node_modules/es5-ext/string/#/contains/shim.js"(exports2, module2) {
    "use strict";
    var indexOf = String.prototype.indexOf;
    module2.exports = function(searchString) {
      return indexOf.call(this, searchString, arguments[1]) > -1;
    };
  }
});

// node_modules/es5-ext/string/#/contains/index.js
var require_contains = __commonJS({
  "node_modules/es5-ext/string/#/contains/index.js"(exports2, module2) {
    "use strict";
    module2.exports = require_is_implemented4()() ? String.prototype.contains : require_shim4();
  }
});

// node_modules/d/index.js
var require_d = __commonJS({
  "node_modules/d/index.js"(exports2, module2) {
    "use strict";
    var isValue = require_is();
    var isPlainFunction = require_is5();
    var assign = require_assign();
    var normalizeOpts = require_normalize_options();
    var contains = require_contains();
    var d = module2.exports = function(dscr, value) {
      var c, e, w, options, desc;
      if (arguments.length < 2 || typeof dscr !== "string") {
        options = value;
        value = dscr;
        dscr = null;
      } else {
        options = arguments[2];
      }
      if (isValue(dscr)) {
        c = contains.call(dscr, "c");
        e = contains.call(dscr, "e");
        w = contains.call(dscr, "w");
      } else {
        c = w = true;
        e = false;
      }
      desc = { value, configurable: c, enumerable: e, writable: w };
      return !options ? desc : assign(normalizeOpts(options), desc);
    };
    d.gs = function(dscr, get, set) {
      var c, e, options, desc;
      if (typeof dscr !== "string") {
        options = set;
        set = get;
        get = dscr;
        dscr = null;
      } else {
        options = arguments[3];
      }
      if (!isValue(get)) {
        get = void 0;
      } else if (!isPlainFunction(get)) {
        options = get;
        get = set = void 0;
      } else if (!isValue(set)) {
        set = void 0;
      } else if (!isPlainFunction(set)) {
        options = set;
        set = void 0;
      }
      if (isValue(dscr)) {
        c = contains.call(dscr, "c");
        e = contains.call(dscr, "e");
      } else {
        c = true;
        e = false;
      }
      desc = { get, set, configurable: c, enumerable: e };
      return !options ? desc : assign(normalizeOpts(options), desc);
    };
  }
});

// node_modules/event-emitter/index.js
var require_event_emitter = __commonJS({
  "node_modules/event-emitter/index.js"(exports2, module2) {
    "use strict";
    var d = require_d();
    var callable = require_valid_callable();
    var apply = Function.prototype.apply;
    var call = Function.prototype.call;
    var create = Object.create;
    var defineProperty = Object.defineProperty;
    var defineProperties = Object.defineProperties;
    var hasOwnProperty2 = Object.prototype.hasOwnProperty;
    var descriptor = { configurable: true, enumerable: false, writable: true };
    var on;
    var once;
    var off;
    var emit;
    var methods;
    var descriptors;
    var base;
    on = function(type, listener) {
      var data;
      callable(listener);
      if (!hasOwnProperty2.call(this, "__ee__")) {
        data = descriptor.value = create(null);
        defineProperty(this, "__ee__", descriptor);
        descriptor.value = null;
      } else {
        data = this.__ee__;
      }
      if (!data[type]) data[type] = listener;
      else if (typeof data[type] === "object") data[type].push(listener);
      else data[type] = [data[type], listener];
      return this;
    };
    once = function(type, listener) {
      var once2, self2;
      callable(listener);
      self2 = this;
      on.call(this, type, once2 = function() {
        off.call(self2, type, once2);
        apply.call(listener, this, arguments);
      });
      once2.__eeOnceListener__ = listener;
      return this;
    };
    off = function(type, listener) {
      var data, listeners, candidate, i;
      callable(listener);
      if (!hasOwnProperty2.call(this, "__ee__")) return this;
      data = this.__ee__;
      if (!data[type]) return this;
      listeners = data[type];
      if (typeof listeners === "object") {
        for (i = 0; candidate = listeners[i]; ++i) {
          if (candidate === listener || candidate.__eeOnceListener__ === listener) {
            if (listeners.length === 2) data[type] = listeners[i ? 0 : 1];
            else listeners.splice(i, 1);
          }
        }
      } else {
        if (listeners === listener || listeners.__eeOnceListener__ === listener) {
          delete data[type];
        }
      }
      return this;
    };
    emit = function(type) {
      var i, l, listener, listeners, args;
      if (!hasOwnProperty2.call(this, "__ee__")) return;
      listeners = this.__ee__[type];
      if (!listeners) return;
      if (typeof listeners === "object") {
        l = arguments.length;
        args = new Array(l - 1);
        for (i = 1; i < l; ++i) args[i - 1] = arguments[i];
        listeners = listeners.slice();
        for (i = 0; listener = listeners[i]; ++i) {
          apply.call(listener, this, args);
        }
      } else {
        switch (arguments.length) {
          case 1:
            call.call(listeners, this);
            break;
          case 2:
            call.call(listeners, this, arguments[1]);
            break;
          case 3:
            call.call(listeners, this, arguments[1], arguments[2]);
            break;
          default:
            l = arguments.length;
            args = new Array(l - 1);
            for (i = 1; i < l; ++i) {
              args[i - 1] = arguments[i];
            }
            apply.call(listeners, this, args);
        }
      }
    };
    methods = {
      on,
      once,
      off,
      emit
    };
    descriptors = {
      on: d(on),
      once: d(once),
      off: d(off),
      emit: d(emit)
    };
    base = defineProperties({}, descriptors);
    module2.exports = exports2 = function(o) {
      return o == null ? create(base) : defineProperties(Object(o), descriptors);
    };
    exports2.methods = methods;
  }
});

// node_modules/es5-ext/array/from/is-implemented.js
var require_is_implemented5 = __commonJS({
  "node_modules/es5-ext/array/from/is-implemented.js"(exports2, module2) {
    "use strict";
    module2.exports = function() {
      var from = Array.from, arr, result;
      if (typeof from !== "function") return false;
      arr = ["raz", "dwa"];
      result = from(arr);
      return Boolean(result && result !== arr && result[1] === "dwa");
    };
  }
});

// node_modules/ext/global-this/is-implemented.js
var require_is_implemented6 = __commonJS({
  "node_modules/ext/global-this/is-implemented.js"(exports2, module2) {
    "use strict";
    module2.exports = function() {
      if (typeof globalThis !== "object") return false;
      if (!globalThis) return false;
      return globalThis.Array === Array;
    };
  }
});

// node_modules/ext/global-this/implementation.js
var require_implementation = __commonJS({
  "node_modules/ext/global-this/implementation.js"(exports2, module2) {
    var naiveFallback = function() {
      if (typeof self === "object" && self) return self;
      if (typeof window === "object" && window) return window;
      throw new Error("Unable to resolve global `this`");
    };
    module2.exports = function() {
      if (this) return this;
      try {
        Object.defineProperty(Object.prototype, "__global__", {
          get: function() {
            return this;
          },
          configurable: true
        });
      } catch (error) {
        return naiveFallback();
      }
      try {
        if (!__global__) return naiveFallback();
        return __global__;
      } finally {
        delete Object.prototype.__global__;
      }
    }();
  }
});

// node_modules/ext/global-this/index.js
var require_global_this = __commonJS({
  "node_modules/ext/global-this/index.js"(exports2, module2) {
    "use strict";
    module2.exports = require_is_implemented6()() ? globalThis : require_implementation();
  }
});

// node_modules/es6-symbol/is-implemented.js
var require_is_implemented7 = __commonJS({
  "node_modules/es6-symbol/is-implemented.js"(exports2, module2) {
    "use strict";
    var global = require_global_this();
    var validTypes = { object: true, symbol: true };
    module2.exports = function() {
      var Symbol2 = global.Symbol;
      var symbol;
      if (typeof Symbol2 !== "function") return false;
      symbol = Symbol2("test symbol");
      try {
        String(symbol);
      } catch (e) {
        return false;
      }
      if (!validTypes[typeof Symbol2.iterator]) return false;
      if (!validTypes[typeof Symbol2.toPrimitive]) return false;
      if (!validTypes[typeof Symbol2.toStringTag]) return false;
      return true;
    };
  }
});

// node_modules/es6-symbol/is-symbol.js
var require_is_symbol = __commonJS({
  "node_modules/es6-symbol/is-symbol.js"(exports2, module2) {
    "use strict";
    module2.exports = function(value) {
      if (!value) return false;
      if (typeof value === "symbol") return true;
      if (!value.constructor) return false;
      if (value.constructor.name !== "Symbol") return false;
      return value[value.constructor.toStringTag] === "Symbol";
    };
  }
});

// node_modules/es6-symbol/validate-symbol.js
var require_validate_symbol = __commonJS({
  "node_modules/es6-symbol/validate-symbol.js"(exports2, module2) {
    "use strict";
    var isSymbol = require_is_symbol();
    module2.exports = function(value) {
      if (!isSymbol(value)) throw new TypeError(value + " is not a symbol");
      return value;
    };
  }
});

// node_modules/es6-symbol/lib/private/generate-name.js
var require_generate_name = __commonJS({
  "node_modules/es6-symbol/lib/private/generate-name.js"(exports2, module2) {
    "use strict";
    var d = require_d();
    var create = Object.create;
    var defineProperty = Object.defineProperty;
    var objPrototype = Object.prototype;
    var created = create(null);
    module2.exports = function(desc) {
      var postfix = 0, name2, ie11BugWorkaround;
      while (created[desc + (postfix || "")]) ++postfix;
      desc += postfix || "";
      created[desc] = true;
      name2 = "@@" + desc;
      defineProperty(
        objPrototype,
        name2,
        d.gs(null, function(value) {
          if (ie11BugWorkaround) return;
          ie11BugWorkaround = true;
          defineProperty(this, name2, d(value));
          ie11BugWorkaround = false;
        })
      );
      return name2;
    };
  }
});

// node_modules/es6-symbol/lib/private/setup/standard-symbols.js
var require_standard_symbols = __commonJS({
  "node_modules/es6-symbol/lib/private/setup/standard-symbols.js"(exports2, module2) {
    "use strict";
    var d = require_d();
    var NativeSymbol = require_global_this().Symbol;
    module2.exports = function(SymbolPolyfill) {
      return Object.defineProperties(SymbolPolyfill, {
        // To ensure proper interoperability with other native functions (e.g. Array.from)
        // fallback to eventual native implementation of given symbol
        hasInstance: d(
          "",
          NativeSymbol && NativeSymbol.hasInstance || SymbolPolyfill("hasInstance")
        ),
        isConcatSpreadable: d(
          "",
          NativeSymbol && NativeSymbol.isConcatSpreadable || SymbolPolyfill("isConcatSpreadable")
        ),
        iterator: d("", NativeSymbol && NativeSymbol.iterator || SymbolPolyfill("iterator")),
        match: d("", NativeSymbol && NativeSymbol.match || SymbolPolyfill("match")),
        replace: d("", NativeSymbol && NativeSymbol.replace || SymbolPolyfill("replace")),
        search: d("", NativeSymbol && NativeSymbol.search || SymbolPolyfill("search")),
        species: d("", NativeSymbol && NativeSymbol.species || SymbolPolyfill("species")),
        split: d("", NativeSymbol && NativeSymbol.split || SymbolPolyfill("split")),
        toPrimitive: d(
          "",
          NativeSymbol && NativeSymbol.toPrimitive || SymbolPolyfill("toPrimitive")
        ),
        toStringTag: d(
          "",
          NativeSymbol && NativeSymbol.toStringTag || SymbolPolyfill("toStringTag")
        ),
        unscopables: d(
          "",
          NativeSymbol && NativeSymbol.unscopables || SymbolPolyfill("unscopables")
        )
      });
    };
  }
});

// node_modules/es6-symbol/lib/private/setup/symbol-registry.js
var require_symbol_registry = __commonJS({
  "node_modules/es6-symbol/lib/private/setup/symbol-registry.js"(exports2, module2) {
    "use strict";
    var d = require_d();
    var validateSymbol = require_validate_symbol();
    var registry = /* @__PURE__ */ Object.create(null);
    module2.exports = function(SymbolPolyfill) {
      return Object.defineProperties(SymbolPolyfill, {
        for: d(function(key) {
          if (registry[key]) return registry[key];
          return registry[key] = SymbolPolyfill(String(key));
        }),
        keyFor: d(function(symbol) {
          var key;
          validateSymbol(symbol);
          for (key in registry) {
            if (registry[key] === symbol) return key;
          }
          return void 0;
        })
      });
    };
  }
});

// node_modules/es6-symbol/polyfill.js
var require_polyfill = __commonJS({
  "node_modules/es6-symbol/polyfill.js"(exports2, module2) {
    "use strict";
    var d = require_d();
    var validateSymbol = require_validate_symbol();
    var NativeSymbol = require_global_this().Symbol;
    var generateName = require_generate_name();
    var setupStandardSymbols = require_standard_symbols();
    var setupSymbolRegistry = require_symbol_registry();
    var create = Object.create;
    var defineProperties = Object.defineProperties;
    var defineProperty = Object.defineProperty;
    var SymbolPolyfill;
    var HiddenSymbol;
    var isNativeSafe;
    if (typeof NativeSymbol === "function") {
      try {
        String(NativeSymbol());
        isNativeSafe = true;
      } catch (ignore) {
      }
    } else {
      NativeSymbol = null;
    }
    HiddenSymbol = function Symbol2(description) {
      if (this instanceof HiddenSymbol) throw new TypeError("Symbol is not a constructor");
      return SymbolPolyfill(description);
    };
    module2.exports = SymbolPolyfill = function Symbol2(description) {
      var symbol;
      if (this instanceof Symbol2) throw new TypeError("Symbol is not a constructor");
      if (isNativeSafe) return NativeSymbol(description);
      symbol = create(HiddenSymbol.prototype);
      description = description === void 0 ? "" : String(description);
      return defineProperties(symbol, {
        __description__: d("", description),
        __name__: d("", generateName(description))
      });
    };
    setupStandardSymbols(SymbolPolyfill);
    setupSymbolRegistry(SymbolPolyfill);
    defineProperties(HiddenSymbol.prototype, {
      constructor: d(SymbolPolyfill),
      toString: d("", function() {
        return this.__name__;
      })
    });
    defineProperties(SymbolPolyfill.prototype, {
      toString: d(function() {
        return "Symbol (" + validateSymbol(this).__description__ + ")";
      }),
      valueOf: d(function() {
        return validateSymbol(this);
      })
    });
    defineProperty(
      SymbolPolyfill.prototype,
      SymbolPolyfill.toPrimitive,
      d("", function() {
        var symbol = validateSymbol(this);
        if (typeof symbol === "symbol") return symbol;
        return symbol.toString();
      })
    );
    defineProperty(SymbolPolyfill.prototype, SymbolPolyfill.toStringTag, d("c", "Symbol"));
    defineProperty(
      HiddenSymbol.prototype,
      SymbolPolyfill.toStringTag,
      d("c", SymbolPolyfill.prototype[SymbolPolyfill.toStringTag])
    );
    defineProperty(
      HiddenSymbol.prototype,
      SymbolPolyfill.toPrimitive,
      d("c", SymbolPolyfill.prototype[SymbolPolyfill.toPrimitive])
    );
  }
});

// node_modules/es6-symbol/index.js
var require_es6_symbol = __commonJS({
  "node_modules/es6-symbol/index.js"(exports2, module2) {
    "use strict";
    module2.exports = require_is_implemented7()() ? require_global_this().Symbol : require_polyfill();
  }
});

// node_modules/es5-ext/function/is-arguments.js
var require_is_arguments = __commonJS({
  "node_modules/es5-ext/function/is-arguments.js"(exports2, module2) {
    "use strict";
    var objToString = Object.prototype.toString;
    var id = objToString.call(/* @__PURE__ */ function() {
      return arguments;
    }());
    module2.exports = function(value) {
      return objToString.call(value) === id;
    };
  }
});

// node_modules/es5-ext/function/is-function.js
var require_is_function = __commonJS({
  "node_modules/es5-ext/function/is-function.js"(exports2, module2) {
    "use strict";
    var objToString = Object.prototype.toString;
    var isFunctionStringTag = RegExp.prototype.test.bind(/^[object [A-Za-z0-9]*Function]$/);
    module2.exports = function(value) {
      return typeof value === "function" && isFunctionStringTag(objToString.call(value));
    };
  }
});

// node_modules/es5-ext/string/is-string.js
var require_is_string = __commonJS({
  "node_modules/es5-ext/string/is-string.js"(exports2, module2) {
    "use strict";
    var objToString = Object.prototype.toString;
    var id = objToString.call("");
    module2.exports = function(value) {
      return typeof value === "string" || value && typeof value === "object" && (value instanceof String || objToString.call(value) === id) || false;
    };
  }
});

// node_modules/es5-ext/array/from/shim.js
var require_shim5 = __commonJS({
  "node_modules/es5-ext/array/from/shim.js"(exports2, module2) {
    "use strict";
    var iteratorSymbol = require_es6_symbol().iterator;
    var isArguments = require_is_arguments();
    var isFunction = require_is_function();
    var toPosInt = require_to_pos_integer();
    var callable = require_valid_callable();
    var validValue = require_valid_value();
    var isValue = require_is_value();
    var isString = require_is_string();
    var isArray = Array.isArray;
    var call = Function.prototype.call;
    var desc = { configurable: true, enumerable: true, writable: true, value: null };
    var defineProperty = Object.defineProperty;
    module2.exports = function(arrayLike) {
      var mapFn = arguments[1], thisArg = arguments[2], Context, i, j, arr, length, code, iterator, result, getIterator, value;
      arrayLike = Object(validValue(arrayLike));
      if (isValue(mapFn)) callable(mapFn);
      if (!this || this === Array || !isFunction(this)) {
        if (!mapFn) {
          if (isArguments(arrayLike)) {
            length = arrayLike.length;
            if (length !== 1) return Array.apply(null, arrayLike);
            arr = new Array(1);
            arr[0] = arrayLike[0];
            return arr;
          }
          if (isArray(arrayLike)) {
            arr = new Array(length = arrayLike.length);
            for (i = 0; i < length; ++i) arr[i] = arrayLike[i];
            return arr;
          }
        }
        arr = [];
      } else {
        Context = this;
      }
      if (!isArray(arrayLike)) {
        if ((getIterator = arrayLike[iteratorSymbol]) !== void 0) {
          iterator = callable(getIterator).call(arrayLike);
          if (Context) arr = new Context();
          result = iterator.next();
          i = 0;
          while (!result.done) {
            value = mapFn ? call.call(mapFn, thisArg, result.value, i) : result.value;
            if (Context) {
              desc.value = value;
              defineProperty(arr, i, desc);
            } else {
              arr[i] = value;
            }
            result = iterator.next();
            ++i;
          }
          length = i;
        } else if (isString(arrayLike)) {
          length = arrayLike.length;
          if (Context) arr = new Context();
          for (i = 0, j = 0; i < length; ++i) {
            value = arrayLike[i];
            if (i + 1 < length) {
              code = value.charCodeAt(0);
              if (code >= 55296 && code <= 56319) value += arrayLike[++i];
            }
            value = mapFn ? call.call(mapFn, thisArg, value, j) : value;
            if (Context) {
              desc.value = value;
              defineProperty(arr, j, desc);
            } else {
              arr[j] = value;
            }
            ++j;
          }
          length = j;
        }
      }
      if (length === void 0) {
        length = toPosInt(arrayLike.length);
        if (Context) arr = new Context(length);
        for (i = 0; i < length; ++i) {
          value = mapFn ? call.call(mapFn, thisArg, arrayLike[i], i) : arrayLike[i];
          if (Context) {
            desc.value = value;
            defineProperty(arr, i, desc);
          } else {
            arr[i] = value;
          }
        }
      }
      if (Context) {
        desc.value = null;
        arr.length = length;
      }
      return arr;
    };
  }
});

// node_modules/es5-ext/array/from/index.js
var require_from = __commonJS({
  "node_modules/es5-ext/array/from/index.js"(exports2, module2) {
    "use strict";
    module2.exports = require_is_implemented5()() ? Array.from : require_shim5();
  }
});

// node_modules/es5-ext/array/to-array.js
var require_to_array = __commonJS({
  "node_modules/es5-ext/array/to-array.js"(exports2, module2) {
    "use strict";
    var from = require_from();
    var isArray = Array.isArray;
    module2.exports = function(arrayLike) {
      return isArray(arrayLike) ? arrayLike : from(arrayLike);
    };
  }
});

// node_modules/memoizee/lib/resolve-resolve.js
var require_resolve_resolve = __commonJS({
  "node_modules/memoizee/lib/resolve-resolve.js"(exports2, module2) {
    "use strict";
    var toArray = require_to_array();
    var isValue = require_is_value();
    var callable = require_valid_callable();
    var slice = Array.prototype.slice;
    var resolveArgs;
    resolveArgs = function(args) {
      return this.map(function(resolve, i) {
        return resolve ? resolve(args[i]) : args[i];
      }).concat(
        slice.call(args, this.length)
      );
    };
    module2.exports = function(resolvers) {
      resolvers = toArray(resolvers);
      resolvers.forEach(function(resolve) {
        if (isValue(resolve)) callable(resolve);
      });
      return resolveArgs.bind(resolvers);
    };
  }
});

// node_modules/memoizee/lib/resolve-normalize.js
var require_resolve_normalize = __commonJS({
  "node_modules/memoizee/lib/resolve-normalize.js"(exports2, module2) {
    "use strict";
    var callable = require_valid_callable();
    module2.exports = function(userNormalizer) {
      var normalizer;
      if (typeof userNormalizer === "function") return { set: userNormalizer, get: userNormalizer };
      normalizer = { get: callable(userNormalizer.get) };
      if (userNormalizer.set !== void 0) {
        normalizer.set = callable(userNormalizer.set);
        if (userNormalizer.delete) normalizer.delete = callable(userNormalizer.delete);
        if (userNormalizer.clear) normalizer.clear = callable(userNormalizer.clear);
        return normalizer;
      }
      normalizer.set = normalizer.get;
      return normalizer;
    };
  }
});

// node_modules/memoizee/lib/configure-map.js
var require_configure_map = __commonJS({
  "node_modules/memoizee/lib/configure-map.js"(exports2, module2) {
    "use strict";
    var customError = require_custom();
    var defineLength = require_define_length();
    var d = require_d();
    var ee = require_event_emitter().methods;
    var resolveResolve = require_resolve_resolve();
    var resolveNormalize = require_resolve_normalize();
    var apply = Function.prototype.apply;
    var call = Function.prototype.call;
    var create = Object.create;
    var defineProperties = Object.defineProperties;
    var on = ee.on;
    var emit = ee.emit;
    module2.exports = function(original, length, options) {
      var cache = create(null), conf, memLength, get, set, del, clear, extDel, extGet, extHas, normalizer, getListeners, setListeners, deleteListeners, memoized, resolve;
      if (length !== false) memLength = length;
      else if (isNaN(original.length)) memLength = 1;
      else memLength = original.length;
      if (options.normalizer) {
        normalizer = resolveNormalize(options.normalizer);
        get = normalizer.get;
        set = normalizer.set;
        del = normalizer.delete;
        clear = normalizer.clear;
      }
      if (options.resolvers != null) resolve = resolveResolve(options.resolvers);
      if (get) {
        memoized = defineLength(function(arg) {
          var id, result, args = arguments;
          if (resolve) args = resolve(args);
          id = get(args);
          if (id !== null) {
            if (hasOwnProperty.call(cache, id)) {
              if (getListeners) conf.emit("get", id, args, this);
              return cache[id];
            }
          }
          if (args.length === 1) result = call.call(original, this, args[0]);
          else result = apply.call(original, this, args);
          if (id === null) {
            id = get(args);
            if (id !== null) throw customError("Circular invocation", "CIRCULAR_INVOCATION");
            id = set(args);
          } else if (hasOwnProperty.call(cache, id)) {
            throw customError("Circular invocation", "CIRCULAR_INVOCATION");
          }
          cache[id] = result;
          if (setListeners) conf.emit("set", id, null, result);
          return result;
        }, memLength);
      } else if (length === 0) {
        memoized = function() {
          var result;
          if (hasOwnProperty.call(cache, "data")) {
            if (getListeners) conf.emit("get", "data", arguments, this);
            return cache.data;
          }
          if (arguments.length) result = apply.call(original, this, arguments);
          else result = call.call(original, this);
          if (hasOwnProperty.call(cache, "data")) {
            throw customError("Circular invocation", "CIRCULAR_INVOCATION");
          }
          cache.data = result;
          if (setListeners) conf.emit("set", "data", null, result);
          return result;
        };
      } else {
        memoized = function(arg) {
          var result, args = arguments, id;
          if (resolve) args = resolve(arguments);
          id = String(args[0]);
          if (hasOwnProperty.call(cache, id)) {
            if (getListeners) conf.emit("get", id, args, this);
            return cache[id];
          }
          if (args.length === 1) result = call.call(original, this, args[0]);
          else result = apply.call(original, this, args);
          if (hasOwnProperty.call(cache, id)) {
            throw customError("Circular invocation", "CIRCULAR_INVOCATION");
          }
          cache[id] = result;
          if (setListeners) conf.emit("set", id, null, result);
          return result;
        };
      }
      conf = {
        original,
        memoized,
        profileName: options.profileName,
        get: function(args) {
          if (resolve) args = resolve(args);
          if (get) return get(args);
          return String(args[0]);
        },
        has: function(id) {
          return hasOwnProperty.call(cache, id);
        },
        delete: function(id) {
          var result;
          if (!hasOwnProperty.call(cache, id)) return;
          if (del) del(id);
          result = cache[id];
          delete cache[id];
          if (deleteListeners) conf.emit("delete", id, result);
        },
        clear: function() {
          var oldCache = cache;
          if (clear) clear();
          cache = create(null);
          conf.emit("clear", oldCache);
        },
        on: function(type, listener) {
          if (type === "get") getListeners = true;
          else if (type === "set") setListeners = true;
          else if (type === "delete") deleteListeners = true;
          return on.call(this, type, listener);
        },
        emit,
        updateEnv: function() {
          original = conf.original;
        }
      };
      if (get) {
        extDel = defineLength(function(arg) {
          var id, args = arguments;
          if (resolve) args = resolve(args);
          id = get(args);
          if (id === null) return;
          conf.delete(id);
        }, memLength);
      } else if (length === 0) {
        extDel = function() {
          return conf.delete("data");
        };
      } else {
        extDel = function(arg) {
          if (resolve) arg = resolve(arguments)[0];
          return conf.delete(arg);
        };
      }
      extGet = defineLength(function() {
        var id, args = arguments;
        if (length === 0) return cache.data;
        if (resolve) args = resolve(args);
        if (get) id = get(args);
        else id = String(args[0]);
        return cache[id];
      });
      extHas = defineLength(function() {
        var id, args = arguments;
        if (length === 0) return conf.has("data");
        if (resolve) args = resolve(args);
        if (get) id = get(args);
        else id = String(args[0]);
        if (id === null) return false;
        return conf.has(id);
      });
      defineProperties(memoized, {
        __memoized__: d(true),
        delete: d(extDel),
        clear: d(conf.clear),
        _get: d(extGet),
        _has: d(extHas)
      });
      return conf;
    };
  }
});

// node_modules/memoizee/plain.js
var require_plain = __commonJS({
  "node_modules/memoizee/plain.js"(exports2, module2) {
    "use strict";
    var callable = require_valid_callable();
    var forEach = require_for_each();
    var extensions = require_registered_extensions();
    var configure = require_configure_map();
    var resolveLength = require_resolve_length();
    module2.exports = function self2(fn) {
      var options, length, conf;
      callable(fn);
      options = Object(arguments[1]);
      if (options.async && options.promise) {
        throw new Error("Options 'async' and 'promise' cannot be used together");
      }
      if (hasOwnProperty.call(fn, "__memoized__") && !options.force) return fn;
      length = resolveLength(options.length, fn.length, options.async && extensions.async);
      conf = configure(fn, length, options);
      forEach(extensions, function(extFn, name2) {
        if (options[name2]) extFn(options[name2], conf, options);
      });
      if (self2.__profiler__) self2.__profiler__(conf);
      conf.updateEnv();
      return conf.memoized;
    };
  }
});

// node_modules/memoizee/normalizers/primitive.js
var require_primitive = __commonJS({
  "node_modules/memoizee/normalizers/primitive.js"(exports2, module2) {
    "use strict";
    module2.exports = function(args) {
      var id, i, length = args.length;
      if (!length) return "";
      id = String(args[i = 0]);
      while (--length) id += "" + args[++i];
      return id;
    };
  }
});

// node_modules/memoizee/normalizers/get-primitive-fixed.js
var require_get_primitive_fixed = __commonJS({
  "node_modules/memoizee/normalizers/get-primitive-fixed.js"(exports2, module2) {
    "use strict";
    module2.exports = function(length) {
      if (!length) {
        return function() {
          return "";
        };
      }
      return function(args) {
        var id = String(args[0]), i = 0, currentLength = length;
        while (--currentLength) {
          id += "" + args[++i];
        }
        return id;
      };
    };
  }
});

// node_modules/es5-ext/number/is-nan/is-implemented.js
var require_is_implemented8 = __commonJS({
  "node_modules/es5-ext/number/is-nan/is-implemented.js"(exports2, module2) {
    "use strict";
    module2.exports = function() {
      var numberIsNaN = Number.isNaN;
      if (typeof numberIsNaN !== "function") return false;
      return !numberIsNaN({}) && numberIsNaN(NaN) && !numberIsNaN(34);
    };
  }
});

// node_modules/es5-ext/number/is-nan/shim.js
var require_shim6 = __commonJS({
  "node_modules/es5-ext/number/is-nan/shim.js"(exports2, module2) {
    "use strict";
    module2.exports = function(value) {
      return value !== value;
    };
  }
});

// node_modules/es5-ext/number/is-nan/index.js
var require_is_nan = __commonJS({
  "node_modules/es5-ext/number/is-nan/index.js"(exports2, module2) {
    "use strict";
    module2.exports = require_is_implemented8()() ? Number.isNaN : require_shim6();
  }
});

// node_modules/es5-ext/array/#/e-index-of.js
var require_e_index_of = __commonJS({
  "node_modules/es5-ext/array/#/e-index-of.js"(exports2, module2) {
    "use strict";
    var numberIsNaN = require_is_nan();
    var toPosInt = require_to_pos_integer();
    var value = require_valid_value();
    var indexOf = Array.prototype.indexOf;
    var objHasOwnProperty = Object.prototype.hasOwnProperty;
    var abs = Math.abs;
    var floor = Math.floor;
    module2.exports = function(searchElement) {
      var i, length, fromIndex, val;
      if (!numberIsNaN(searchElement)) return indexOf.apply(this, arguments);
      length = toPosInt(value(this).length);
      fromIndex = arguments[1];
      if (isNaN(fromIndex)) fromIndex = 0;
      else if (fromIndex >= 0) fromIndex = floor(fromIndex);
      else fromIndex = toPosInt(this.length) - floor(abs(fromIndex));
      for (i = fromIndex; i < length; ++i) {
        if (objHasOwnProperty.call(this, i)) {
          val = this[i];
          if (numberIsNaN(val)) return i;
        }
      }
      return -1;
    };
  }
});

// node_modules/memoizee/normalizers/get.js
var require_get = __commonJS({
  "node_modules/memoizee/normalizers/get.js"(exports2, module2) {
    "use strict";
    var indexOf = require_e_index_of();
    var create = Object.create;
    module2.exports = function() {
      var lastId = 0, map = [], cache = create(null);
      return {
        get: function(args) {
          var index = 0, set = map, i, length = args.length;
          if (length === 0) return set[length] || null;
          if (set = set[length]) {
            while (index < length - 1) {
              i = indexOf.call(set[0], args[index]);
              if (i === -1) return null;
              set = set[1][i];
              ++index;
            }
            i = indexOf.call(set[0], args[index]);
            if (i === -1) return null;
            return set[1][i] || null;
          }
          return null;
        },
        set: function(args) {
          var index = 0, set = map, i, length = args.length;
          if (length === 0) {
            set[length] = ++lastId;
          } else {
            if (!set[length]) {
              set[length] = [[], []];
            }
            set = set[length];
            while (index < length - 1) {
              i = indexOf.call(set[0], args[index]);
              if (i === -1) {
                i = set[0].push(args[index]) - 1;
                set[1].push([[], []]);
              }
              set = set[1][i];
              ++index;
            }
            i = indexOf.call(set[0], args[index]);
            if (i === -1) {
              i = set[0].push(args[index]) - 1;
            }
            set[1][i] = ++lastId;
          }
          cache[lastId] = args;
          return lastId;
        },
        delete: function(id) {
          var index = 0, set = map, i, args = cache[id], length = args.length, path = [];
          if (length === 0) {
            delete set[length];
          } else if (set = set[length]) {
            while (index < length - 1) {
              i = indexOf.call(set[0], args[index]);
              if (i === -1) {
                return;
              }
              path.push(set, i);
              set = set[1][i];
              ++index;
            }
            i = indexOf.call(set[0], args[index]);
            if (i === -1) {
              return;
            }
            id = set[1][i];
            set[0].splice(i, 1);
            set[1].splice(i, 1);
            while (!set[0].length && path.length) {
              i = path.pop();
              set = path.pop();
              set[0].splice(i, 1);
              set[1].splice(i, 1);
            }
          }
          delete cache[id];
        },
        clear: function() {
          map = [];
          cache = create(null);
        }
      };
    };
  }
});

// node_modules/memoizee/normalizers/get-1.js
var require_get_1 = __commonJS({
  "node_modules/memoizee/normalizers/get-1.js"(exports2, module2) {
    "use strict";
    var indexOf = require_e_index_of();
    module2.exports = function() {
      var lastId = 0, argsMap = [], cache = [];
      return {
        get: function(args) {
          var index = indexOf.call(argsMap, args[0]);
          return index === -1 ? null : cache[index];
        },
        set: function(args) {
          argsMap.push(args[0]);
          cache.push(++lastId);
          return lastId;
        },
        delete: function(id) {
          var index = indexOf.call(cache, id);
          if (index !== -1) {
            argsMap.splice(index, 1);
            cache.splice(index, 1);
          }
        },
        clear: function() {
          argsMap = [];
          cache = [];
        }
      };
    };
  }
});

// node_modules/memoizee/normalizers/get-fixed.js
var require_get_fixed = __commonJS({
  "node_modules/memoizee/normalizers/get-fixed.js"(exports2, module2) {
    "use strict";
    var indexOf = require_e_index_of();
    var create = Object.create;
    module2.exports = function(length) {
      var lastId = 0, map = [[], []], cache = create(null);
      return {
        get: function(args) {
          var index = 0, set = map, i;
          while (index < length - 1) {
            i = indexOf.call(set[0], args[index]);
            if (i === -1) return null;
            set = set[1][i];
            ++index;
          }
          i = indexOf.call(set[0], args[index]);
          if (i === -1) return null;
          return set[1][i] || null;
        },
        set: function(args) {
          var index = 0, set = map, i;
          while (index < length - 1) {
            i = indexOf.call(set[0], args[index]);
            if (i === -1) {
              i = set[0].push(args[index]) - 1;
              set[1].push([[], []]);
            }
            set = set[1][i];
            ++index;
          }
          i = indexOf.call(set[0], args[index]);
          if (i === -1) {
            i = set[0].push(args[index]) - 1;
          }
          set[1][i] = ++lastId;
          cache[lastId] = args;
          return lastId;
        },
        delete: function(id) {
          var index = 0, set = map, i, path = [], args = cache[id];
          while (index < length - 1) {
            i = indexOf.call(set[0], args[index]);
            if (i === -1) {
              return;
            }
            path.push(set, i);
            set = set[1][i];
            ++index;
          }
          i = indexOf.call(set[0], args[index]);
          if (i === -1) {
            return;
          }
          id = set[1][i];
          set[0].splice(i, 1);
          set[1].splice(i, 1);
          while (!set[0].length && path.length) {
            i = path.pop();
            set = path.pop();
            set[0].splice(i, 1);
            set[1].splice(i, 1);
          }
          delete cache[id];
        },
        clear: function() {
          map = [[], []];
          cache = create(null);
        }
      };
    };
  }
});

// node_modules/es5-ext/object/map.js
var require_map = __commonJS({
  "node_modules/es5-ext/object/map.js"(exports2, module2) {
    "use strict";
    var callable = require_valid_callable();
    var forEach = require_for_each();
    var call = Function.prototype.call;
    module2.exports = function(obj, cb) {
      var result = {}, thisArg = arguments[2];
      callable(cb);
      forEach(obj, function(value, key, targetObj, index) {
        result[key] = call.call(cb, thisArg, value, key, targetObj, index);
      });
      return result;
    };
  }
});

// node_modules/next-tick/index.js
var require_next_tick = __commonJS({
  "node_modules/next-tick/index.js"(exports2, module2) {
    "use strict";
    var ensureCallable = function(fn) {
      if (typeof fn !== "function") throw new TypeError(fn + " is not a function");
      return fn;
    };
    var byObserver = function(Observer) {
      var node = document.createTextNode(""), queue, currentQueue, i = 0;
      new Observer(function() {
        var callback;
        if (!queue) {
          if (!currentQueue) return;
          queue = currentQueue;
        } else if (currentQueue) {
          queue = currentQueue.concat(queue);
        }
        currentQueue = queue;
        queue = null;
        if (typeof currentQueue === "function") {
          callback = currentQueue;
          currentQueue = null;
          callback();
          return;
        }
        node.data = i = ++i % 2;
        while (currentQueue) {
          callback = currentQueue.shift();
          if (!currentQueue.length) currentQueue = null;
          callback();
        }
      }).observe(node, { characterData: true });
      return function(fn) {
        ensureCallable(fn);
        if (queue) {
          if (typeof queue === "function") queue = [queue, fn];
          else queue.push(fn);
          return;
        }
        queue = fn;
        node.data = i = ++i % 2;
      };
    };
    module2.exports = function() {
      if (typeof process === "object" && process && typeof process.nextTick === "function") {
        return process.nextTick;
      }
      if (typeof queueMicrotask === "function") {
        return function(cb) {
          queueMicrotask(ensureCallable(cb));
        };
      }
      if (typeof document === "object" && document) {
        if (typeof MutationObserver === "function") return byObserver(MutationObserver);
        if (typeof WebKitMutationObserver === "function") return byObserver(WebKitMutationObserver);
      }
      if (typeof setImmediate === "function") {
        return function(cb) {
          setImmediate(ensureCallable(cb));
        };
      }
      if (typeof setTimeout === "function" || typeof setTimeout === "object") {
        return function(cb) {
          setTimeout(ensureCallable(cb), 0);
        };
      }
      return null;
    }();
  }
});

// node_modules/memoizee/ext/async.js
var require_async = __commonJS({
  "node_modules/memoizee/ext/async.js"() {
    "use strict";
    var aFrom = require_from();
    var objectMap = require_map();
    var mixin = require_mixin();
    var defineLength = require_define_length();
    var nextTick = require_next_tick();
    var slice = Array.prototype.slice;
    var apply = Function.prototype.apply;
    var create = Object.create;
    require_registered_extensions().async = function(tbi, conf) {
      var waiting = create(null), cache = create(null), base = conf.memoized, original = conf.original, currentCallback, currentContext, currentArgs;
      conf.memoized = defineLength(function(arg) {
        var args = arguments, last = args[args.length - 1];
        if (typeof last === "function") {
          currentCallback = last;
          args = slice.call(args, 0, -1);
        }
        return base.apply(currentContext = this, currentArgs = args);
      }, base);
      try {
        mixin(conf.memoized, base);
      } catch (ignore) {
      }
      conf.on("get", function(id) {
        var cb, context, args;
        if (!currentCallback) return;
        if (waiting[id]) {
          if (typeof waiting[id] === "function") waiting[id] = [waiting[id], currentCallback];
          else waiting[id].push(currentCallback);
          currentCallback = null;
          return;
        }
        cb = currentCallback;
        context = currentContext;
        args = currentArgs;
        currentCallback = currentContext = currentArgs = null;
        nextTick(function() {
          var data;
          if (hasOwnProperty.call(cache, id)) {
            data = cache[id];
            conf.emit("getasync", id, args, context);
            apply.call(cb, data.context, data.args);
          } else {
            currentCallback = cb;
            currentContext = context;
            currentArgs = args;
            base.apply(context, args);
          }
        });
      });
      conf.original = function() {
        var args, cb, origCb, result;
        if (!currentCallback) return apply.call(original, this, arguments);
        args = aFrom(arguments);
        cb = function self2(err) {
          var cb2, args2, id = self2.id;
          if (id == null) {
            nextTick(apply.bind(self2, this, arguments));
            return void 0;
          }
          delete self2.id;
          cb2 = waiting[id];
          delete waiting[id];
          if (!cb2) {
            return void 0;
          }
          args2 = aFrom(arguments);
          if (conf.has(id)) {
            if (err) {
              conf.delete(id);
            } else {
              cache[id] = { context: this, args: args2 };
              conf.emit("setasync", id, typeof cb2 === "function" ? 1 : cb2.length);
            }
          }
          if (typeof cb2 === "function") {
            result = apply.call(cb2, this, args2);
          } else {
            cb2.forEach(function(cb3) {
              result = apply.call(cb3, this, args2);
            }, this);
          }
          return result;
        };
        origCb = currentCallback;
        currentCallback = currentContext = currentArgs = null;
        args.push(cb);
        result = apply.call(original, this, args);
        cb.cb = origCb;
        currentCallback = cb;
        return result;
      };
      conf.on("set", function(id) {
        if (!currentCallback) {
          conf.delete(id);
          return;
        }
        if (waiting[id]) {
          if (typeof waiting[id] === "function") waiting[id] = [waiting[id], currentCallback.cb];
          else waiting[id].push(currentCallback.cb);
        } else {
          waiting[id] = currentCallback.cb;
        }
        delete currentCallback.cb;
        currentCallback.id = id;
        currentCallback = null;
      });
      conf.on("delete", function(id) {
        var result;
        if (hasOwnProperty.call(waiting, id)) return;
        if (!cache[id]) return;
        result = cache[id];
        delete cache[id];
        conf.emit("deleteasync", id, slice.call(result.args, 1));
      });
      conf.on("clear", function() {
        var oldCache = cache;
        cache = create(null);
        conf.emit(
          "clearasync",
          objectMap(oldCache, function(data) {
            return slice.call(data.args, 1);
          })
        );
      });
    };
  }
});

// node_modules/es5-ext/object/primitive-set.js
var require_primitive_set = __commonJS({
  "node_modules/es5-ext/object/primitive-set.js"(exports2, module2) {
    "use strict";
    var forEach = Array.prototype.forEach;
    var create = Object.create;
    module2.exports = function(arg) {
      var set = create(null);
      forEach.call(arguments, function(name2) {
        set[name2] = true;
      });
      return set;
    };
  }
});

// node_modules/es5-ext/object/is-callable.js
var require_is_callable = __commonJS({
  "node_modules/es5-ext/object/is-callable.js"(exports2, module2) {
    "use strict";
    module2.exports = function(obj) {
      return typeof obj === "function";
    };
  }
});

// node_modules/es5-ext/object/validate-stringifiable.js
var require_validate_stringifiable = __commonJS({
  "node_modules/es5-ext/object/validate-stringifiable.js"(exports2, module2) {
    "use strict";
    var isCallable = require_is_callable();
    module2.exports = function(stringifiable) {
      try {
        if (stringifiable && isCallable(stringifiable.toString)) return stringifiable.toString();
        return String(stringifiable);
      } catch (e) {
        throw new TypeError("Passed argument cannot be stringifed");
      }
    };
  }
});

// node_modules/es5-ext/object/validate-stringifiable-value.js
var require_validate_stringifiable_value = __commonJS({
  "node_modules/es5-ext/object/validate-stringifiable-value.js"(exports2, module2) {
    "use strict";
    var ensureValue = require_valid_value();
    var stringifiable = require_validate_stringifiable();
    module2.exports = function(value) {
      return stringifiable(ensureValue(value));
    };
  }
});

// node_modules/es5-ext/safe-to-string.js
var require_safe_to_string = __commonJS({
  "node_modules/es5-ext/safe-to-string.js"(exports2, module2) {
    "use strict";
    var isCallable = require_is_callable();
    module2.exports = function(value) {
      try {
        if (value && isCallable(value.toString)) return value.toString();
        return String(value);
      } catch (e) {
        return "<Non-coercible to string value>";
      }
    };
  }
});

// node_modules/es5-ext/to-short-string-representation.js
var require_to_short_string_representation = __commonJS({
  "node_modules/es5-ext/to-short-string-representation.js"(exports2, module2) {
    "use strict";
    var safeToString = require_safe_to_string();
    var reNewLine = /[\n\r\u2028\u2029]/g;
    module2.exports = function(value) {
      var string = safeToString(value);
      if (string.length > 100) string = string.slice(0, 99) + "\u2026";
      string = string.replace(reNewLine, function(char) {
        return JSON.stringify(char).slice(1, -1);
      });
      return string;
    };
  }
});

// node_modules/is-promise/index.js
var require_is_promise = __commonJS({
  "node_modules/is-promise/index.js"(exports2, module2) {
    module2.exports = isPromise;
    module2.exports.default = isPromise;
    function isPromise(obj) {
      return !!obj && (typeof obj === "object" || typeof obj === "function") && typeof obj.then === "function";
    }
  }
});

// node_modules/memoizee/ext/promise.js
var require_promise = __commonJS({
  "node_modules/memoizee/ext/promise.js"() {
    "use strict";
    var objectMap = require_map();
    var primitiveSet = require_primitive_set();
    var ensureString = require_validate_stringifiable_value();
    var toShortString = require_to_short_string_representation();
    var isPromise = require_is_promise();
    var nextTick = require_next_tick();
    var create = Object.create;
    var supportedModes = primitiveSet("then", "then:finally", "done", "done:finally");
    require_registered_extensions().promise = function(mode, conf) {
      var waiting = create(null), cache = create(null), promises = create(null);
      if (mode === true) {
        mode = null;
      } else {
        mode = ensureString(mode);
        if (!supportedModes[mode]) {
          throw new TypeError("'" + toShortString(mode) + "' is not valid promise mode");
        }
      }
      conf.on("set", function(id, ignore, promise) {
        var isFailed = false;
        if (!isPromise(promise)) {
          cache[id] = promise;
          conf.emit("setasync", id, 1);
          return;
        }
        waiting[id] = 1;
        promises[id] = promise;
        var onSuccess = function(result) {
          var count = waiting[id];
          if (isFailed) {
            throw new Error(
              "Memoizee error: Detected unordered then|done & finally resolution, which in turn makes proper detection of success/failure impossible (when in 'done:finally' mode)\nConsider to rely on 'then' or 'done' mode instead."
            );
          }
          if (!count) return;
          delete waiting[id];
          cache[id] = result;
          conf.emit("setasync", id, count);
        };
        var onFailure = function() {
          isFailed = true;
          if (!waiting[id]) return;
          delete waiting[id];
          delete promises[id];
          conf.delete(id);
        };
        var resolvedMode = mode;
        if (!resolvedMode) resolvedMode = "then";
        if (resolvedMode === "then") {
          var nextTickFailure = function() {
            nextTick(onFailure);
          };
          promise = promise.then(function(result) {
            nextTick(onSuccess.bind(this, result));
          }, nextTickFailure);
          if (typeof promise.finally === "function") {
            promise.finally(nextTickFailure);
          }
        } else if (resolvedMode === "done") {
          if (typeof promise.done !== "function") {
            throw new Error(
              "Memoizee error: Retrieved promise does not implement 'done' in 'done' mode"
            );
          }
          promise.done(onSuccess, onFailure);
        } else if (resolvedMode === "done:finally") {
          if (typeof promise.done !== "function") {
            throw new Error(
              "Memoizee error: Retrieved promise does not implement 'done' in 'done:finally' mode"
            );
          }
          if (typeof promise.finally !== "function") {
            throw new Error(
              "Memoizee error: Retrieved promise does not implement 'finally' in 'done:finally' mode"
            );
          }
          promise.done(onSuccess);
          promise.finally(onFailure);
        }
      });
      conf.on("get", function(id, args, context) {
        var promise;
        if (waiting[id]) {
          ++waiting[id];
          return;
        }
        promise = promises[id];
        var emit = function() {
          conf.emit("getasync", id, args, context);
        };
        if (isPromise(promise)) {
          if (typeof promise.done === "function") promise.done(emit);
          else {
            promise.then(function() {
              nextTick(emit);
            });
          }
        } else {
          emit();
        }
      });
      conf.on("delete", function(id) {
        delete promises[id];
        if (waiting[id]) {
          delete waiting[id];
          return;
        }
        if (!hasOwnProperty.call(cache, id)) return;
        var result = cache[id];
        delete cache[id];
        conf.emit("deleteasync", id, [result]);
      });
      conf.on("clear", function() {
        var oldCache = cache;
        cache = create(null);
        waiting = create(null);
        promises = create(null);
        conf.emit("clearasync", objectMap(oldCache, function(data) {
          return [data];
        }));
      });
    };
  }
});

// node_modules/memoizee/ext/dispose.js
var require_dispose = __commonJS({
  "node_modules/memoizee/ext/dispose.js"() {
    "use strict";
    var callable = require_valid_callable();
    var forEach = require_for_each();
    var extensions = require_registered_extensions();
    var apply = Function.prototype.apply;
    extensions.dispose = function(dispose, conf, options) {
      var del;
      callable(dispose);
      if (options.async && extensions.async || options.promise && extensions.promise) {
        conf.on(
          "deleteasync",
          del = function(id, resultArray) {
            apply.call(dispose, null, resultArray);
          }
        );
        conf.on("clearasync", function(cache) {
          forEach(cache, function(result, id) {
            del(id, result);
          });
        });
        return;
      }
      conf.on("delete", del = function(id, result) {
        dispose(result);
      });
      conf.on("clear", function(cache) {
        forEach(cache, function(result, id) {
          del(id, result);
        });
      });
    };
  }
});

// node_modules/timers-ext/max-timeout.js
var require_max_timeout = __commonJS({
  "node_modules/timers-ext/max-timeout.js"(exports2, module2) {
    "use strict";
    module2.exports = 2147483647;
  }
});

// node_modules/timers-ext/valid-timeout.js
var require_valid_timeout = __commonJS({
  "node_modules/timers-ext/valid-timeout.js"(exports2, module2) {
    "use strict";
    var toPosInt = require_to_pos_integer();
    var maxTimeout = require_max_timeout();
    module2.exports = function(value) {
      value = toPosInt(value);
      if (value > maxTimeout) throw new TypeError(value + " exceeds maximum possible timeout");
      return value;
    };
  }
});

// node_modules/memoizee/ext/max-age.js
var require_max_age = __commonJS({
  "node_modules/memoizee/ext/max-age.js"() {
    "use strict";
    var aFrom = require_from();
    var forEach = require_for_each();
    var nextTick = require_next_tick();
    var isPromise = require_is_promise();
    var timeout = require_valid_timeout();
    var extensions = require_registered_extensions();
    var noop = Function.prototype;
    var max = Math.max;
    var min = Math.min;
    var create = Object.create;
    extensions.maxAge = function(maxAge, conf, options) {
      var timeouts, postfix, preFetchAge, preFetchTimeouts;
      maxAge = timeout(maxAge);
      if (!maxAge) return;
      timeouts = create(null);
      postfix = options.async && extensions.async || options.promise && extensions.promise ? "async" : "";
      conf.on("set" + postfix, function(id) {
        timeouts[id] = setTimeout(function() {
          conf.delete(id);
        }, maxAge);
        if (typeof timeouts[id].unref === "function") timeouts[id].unref();
        if (!preFetchTimeouts) return;
        if (preFetchTimeouts[id]) {
          if (preFetchTimeouts[id] !== "nextTick") clearTimeout(preFetchTimeouts[id]);
        }
        preFetchTimeouts[id] = setTimeout(function() {
          delete preFetchTimeouts[id];
        }, preFetchAge);
        if (typeof preFetchTimeouts[id].unref === "function") preFetchTimeouts[id].unref();
      });
      conf.on("delete" + postfix, function(id) {
        clearTimeout(timeouts[id]);
        delete timeouts[id];
        if (!preFetchTimeouts) return;
        if (preFetchTimeouts[id] !== "nextTick") clearTimeout(preFetchTimeouts[id]);
        delete preFetchTimeouts[id];
      });
      if (options.preFetch) {
        if (options.preFetch === true || isNaN(options.preFetch)) {
          preFetchAge = 0.333;
        } else {
          preFetchAge = max(min(Number(options.preFetch), 1), 0);
        }
        if (preFetchAge) {
          preFetchTimeouts = {};
          preFetchAge = (1 - preFetchAge) * maxAge;
          conf.on("get" + postfix, function(id, args, context) {
            if (!preFetchTimeouts[id]) {
              preFetchTimeouts[id] = "nextTick";
              nextTick(function() {
                var result;
                if (preFetchTimeouts[id] !== "nextTick") return;
                delete preFetchTimeouts[id];
                conf.delete(id);
                if (options.async) {
                  args = aFrom(args);
                  args.push(noop);
                }
                result = conf.memoized.apply(context, args);
                if (options.promise) {
                  if (isPromise(result)) {
                    if (typeof result.done === "function") result.done(noop, noop);
                    else result.then(noop, noop);
                  }
                }
              });
            }
          });
        }
      }
      conf.on("clear" + postfix, function() {
        forEach(timeouts, function(id) {
          clearTimeout(id);
        });
        timeouts = {};
        if (preFetchTimeouts) {
          forEach(preFetchTimeouts, function(id) {
            if (id !== "nextTick") clearTimeout(id);
          });
          preFetchTimeouts = {};
        }
      });
    };
  }
});

// node_modules/lru-queue/index.js
var require_lru_queue = __commonJS({
  "node_modules/lru-queue/index.js"(exports2, module2) {
    "use strict";
    var toPosInt = require_to_pos_integer();
    var create = Object.create;
    var hasOwnProperty2 = Object.prototype.hasOwnProperty;
    module2.exports = function(limit) {
      var size = 0, base = 1, queue = create(null), map = create(null), index = 0, del;
      limit = toPosInt(limit);
      return {
        hit: function(id) {
          var oldIndex = map[id], nuIndex = ++index;
          queue[nuIndex] = id;
          map[id] = nuIndex;
          if (!oldIndex) {
            ++size;
            if (size <= limit) return;
            id = queue[base];
            del(id);
            return id;
          }
          delete queue[oldIndex];
          if (base !== oldIndex) return;
          while (!hasOwnProperty2.call(queue, ++base)) continue;
        },
        delete: del = function(id) {
          var oldIndex = map[id];
          if (!oldIndex) return;
          delete queue[oldIndex];
          delete map[id];
          --size;
          if (base !== oldIndex) return;
          if (!size) {
            index = 0;
            base = 1;
            return;
          }
          while (!hasOwnProperty2.call(queue, ++base)) continue;
        },
        clear: function() {
          size = 0;
          base = 1;
          queue = create(null);
          map = create(null);
          index = 0;
        }
      };
    };
  }
});

// node_modules/memoizee/ext/max.js
var require_max = __commonJS({
  "node_modules/memoizee/ext/max.js"() {
    "use strict";
    var toPosInteger = require_to_pos_integer();
    var lruQueue = require_lru_queue();
    var extensions = require_registered_extensions();
    extensions.max = function(max, conf, options) {
      var postfix, queue, hit;
      max = toPosInteger(max);
      if (!max) return;
      queue = lruQueue(max);
      postfix = options.async && extensions.async || options.promise && extensions.promise ? "async" : "";
      conf.on(
        "set" + postfix,
        hit = function(id) {
          id = queue.hit(id);
          if (id === void 0) return;
          conf.delete(id);
        }
      );
      conf.on("get" + postfix, hit);
      conf.on("delete" + postfix, queue.delete);
      conf.on("clear" + postfix, queue.clear);
    };
  }
});

// node_modules/memoizee/ext/ref-counter.js
var require_ref_counter = __commonJS({
  "node_modules/memoizee/ext/ref-counter.js"() {
    "use strict";
    var d = require_d();
    var extensions = require_registered_extensions();
    var create = Object.create;
    var defineProperties = Object.defineProperties;
    extensions.refCounter = function(ignore, conf, options) {
      var cache, postfix;
      cache = create(null);
      postfix = options.async && extensions.async || options.promise && extensions.promise ? "async" : "";
      conf.on("set" + postfix, function(id, length) {
        cache[id] = length || 1;
      });
      conf.on("get" + postfix, function(id) {
        ++cache[id];
      });
      conf.on("delete" + postfix, function(id) {
        delete cache[id];
      });
      conf.on("clear" + postfix, function() {
        cache = {};
      });
      defineProperties(conf.memoized, {
        deleteRef: d(function() {
          var id = conf.get(arguments);
          if (id === null) return null;
          if (!cache[id]) return null;
          if (!--cache[id]) {
            conf.delete(id);
            return true;
          }
          return false;
        }),
        getRefCount: d(function() {
          var id = conf.get(arguments);
          if (id === null) return 0;
          if (!cache[id]) return 0;
          return cache[id];
        })
      });
    };
  }
});

// node_modules/memoizee/index.js
var require_memoizee = __commonJS({
  "node_modules/memoizee/index.js"(exports2, module2) {
    "use strict";
    var normalizeOpts = require_normalize_options();
    var resolveLength = require_resolve_length();
    var plain = require_plain();
    module2.exports = function(fn) {
      var options = normalizeOpts(arguments[1]), length;
      if (!options.normalizer) {
        length = options.length = resolveLength(options.length, fn.length, options.async);
        if (length !== 0) {
          if (options.primitive) {
            if (length === false) {
              options.normalizer = require_primitive();
            } else if (length > 1) {
              options.normalizer = require_get_primitive_fixed()(length);
            }
          } else if (length === false) options.normalizer = require_get()();
          else if (length === 1) options.normalizer = require_get_1()();
          else options.normalizer = require_get_fixed()(length);
        }
      }
      if (options.async) require_async();
      if (options.promise) require_promise();
      if (options.dispose) require_dispose();
      if (options.maxAge) require_max_age();
      if (options.max) require_max();
      if (options.refCounter) require_ref_counter();
      return plain(fn, options);
    };
  }
});

// js/retext-spell.mjs
var retext_spell_exports = {};
__export(retext_spell_exports, {
  name: () => name,
  plugin: () => plugin
});
module.exports = __toCommonJS(retext_spell_exports);

// node_modules/nlcst-to-string/lib/index.js
var emptyNodes = [];
function toString(value) {
  let index = -1;
  if (!value || !Array.isArray(value) && !value.type) {
    throw new Error("Expected node, not `" + value + "`");
  }
  if ("value" in value) return value.value;
  const children = (Array.isArray(value) ? value : value.children) || emptyNodes;
  const values = [];
  while (++index < children.length) {
    values[index] = toString(children[index]);
  }
  return values.join("");
}

// node_modules/nlcst-is-literal/lib/index.js
var single = [
  "-",
  // Hyphen-minus
  "\u2013",
  // En dash
  "\u2014",
  // Em dash
  ":",
  // Colon
  ";"
  // Semi-colon
];
var pairs = {
  ",": [","],
  "-": ["-"],
  "\u2013": ["\u2013"],
  "\u2014": ["\u2014"],
  '"': ['"'],
  "'": ["'"],
  "\u2018": ["\u2019"],
  "\u201A": ["\u2019"],
  "\u2019": ["\u2019", "\u201A"],
  "\u201C": ["\u201D"],
  "\u201D": ["\u201D"],
  "\u201E": ["\u201D", "\u201C"],
  "\xAB": ["\xBB"],
  "\xBB": ["\xAB"],
  "\u2039": ["\u203A"],
  "\u203A": ["\u2039"],
  "(": [")"],
  "[": ["]"],
  "{": ["}"],
  "\u27E8": ["\u27E9"],
  "\u300C": ["\u300D"]
};
var open = Object.keys(pairs);
function isLiteral(parent, index) {
  if (!(parent && parent.children)) {
    throw new Error("Parent must be a node");
  }
  const siblings = parent.children;
  if (index !== null && typeof index === "object" && "type" in index) {
    index = siblings.indexOf(index);
    if (index === -1) {
      throw new Error("Node must be a child of `parent`");
    }
  }
  if (typeof index !== "number" || Number.isNaN(index)) {
    throw new TypeError("Index must be a number");
  }
  return Boolean(
    !containsWord(parent, -1, index) && siblingDelimiter(parent, index, 1, single) || !containsWord(parent, index, siblings.length) && siblingDelimiter(parent, index, -1, single) || isWrapped(parent, index)
  );
}
function isWrapped(parent, position) {
  const previous = siblingDelimiter(parent, position, -1, open);
  if (previous) {
    return siblingDelimiter(parent, position, 1, pairs[toString(previous)]) !== void 0;
  }
  return false;
}
function siblingDelimiter(parent, position, step, delimiters) {
  let index = position + step;
  while (index > -1 && index < parent.children.length) {
    const sibling = parent.children[index];
    if (sibling.type === "WordNode" || sibling.type === "SourceNode") {
      break;
    }
    if (sibling.type !== "WhiteSpaceNode") {
      return delimiters.includes(toString(sibling)) ? sibling : void 0;
    }
    index += step;
  }
}
function containsWord(parent, start, end) {
  while (++start < end) {
    if (parent.children[start].type === "WordNode") {
      return true;
    }
  }
  return false;
}

// node_modules/retext-spell/lib/index.js
var import_nspell = __toESM(require_lib(), 1);

// node_modules/quotation/index.js
var quotation = (
  /**
   * @type {{
   *   (value: string, open?: string | null | undefined, close?: string | null | undefined): string
   *   (value: ReadonlyArray<string>, open?: string | null | undefined, close?: string | null | undefined): string[]
   * }}
   */
  /**
   * @param {ReadonlyArray<string> | string} value
   * @param {string | null | undefined} open
   * @param {string | null | undefined} close
   * @returns {Array<string> | string}
   */
  function(value, open2, close) {
    const start = open2 || '"';
    const end = close || start;
    let index = -1;
    if (Array.isArray(value)) {
      const list = (
        /** @type {ReadonlyArray<string>} */
        value
      );
      const result = [];
      while (++index < list.length) {
        result[index] = start + list[index] + end;
      }
      return result;
    }
    if (typeof value === "string") {
      return start + value + end;
    }
    throw new TypeError("Expected string or array of strings");
  }
);

// node_modules/unist-util-is/lib/index.js
var convert = (
  // Note: overloads in JSDoc can’t yet use different `@template`s.
  /**
   * @type {(
   *   (<Condition extends string>(test: Condition) => (node: unknown, index?: number | null | undefined, parent?: Parent | null | undefined, context?: unknown) => node is Node & {type: Condition}) &
   *   (<Condition extends Props>(test: Condition) => (node: unknown, index?: number | null | undefined, parent?: Parent | null | undefined, context?: unknown) => node is Node & Condition) &
   *   (<Condition extends TestFunction>(test: Condition) => (node: unknown, index?: number | null | undefined, parent?: Parent | null | undefined, context?: unknown) => node is Node & Predicate<Condition, Node>) &
   *   ((test?: null | undefined) => (node?: unknown, index?: number | null | undefined, parent?: Parent | null | undefined, context?: unknown) => node is Node) &
   *   ((test?: Test) => Check)
   * )}
   */
  /**
   * @param {Test} [test]
   * @returns {Check}
   */
  function(test) {
    if (test === null || test === void 0) {
      return ok;
    }
    if (typeof test === "function") {
      return castFactory(test);
    }
    if (typeof test === "object") {
      return Array.isArray(test) ? anyFactory(test) : propsFactory(test);
    }
    if (typeof test === "string") {
      return typeFactory(test);
    }
    throw new Error("Expected function, string, or object as test");
  }
);
function anyFactory(tests) {
  const checks = [];
  let index = -1;
  while (++index < tests.length) {
    checks[index] = convert(tests[index]);
  }
  return castFactory(any);
  function any(...parameters) {
    let index2 = -1;
    while (++index2 < checks.length) {
      if (checks[index2].apply(this, parameters)) return true;
    }
    return false;
  }
}
function propsFactory(check) {
  const checkAsRecord = (
    /** @type {Record<string, unknown>} */
    check
  );
  return castFactory(all2);
  function all2(node) {
    const nodeAsRecord = (
      /** @type {Record<string, unknown>} */
      /** @type {unknown} */
      node
    );
    let key;
    for (key in check) {
      if (nodeAsRecord[key] !== checkAsRecord[key]) return false;
    }
    return true;
  }
}
function typeFactory(check) {
  return castFactory(type);
  function type(node) {
    return node && node.type === check;
  }
}
function castFactory(testFunction) {
  return check;
  function check(value, index, parent) {
    return Boolean(
      looksLikeANode(value) && testFunction.call(
        this,
        value,
        typeof index === "number" ? index : void 0,
        parent || void 0
      )
    );
  }
}
function ok() {
  return true;
}
function looksLikeANode(value) {
  return value !== null && typeof value === "object" && "type" in value;
}

// node_modules/unist-util-visit-parents/lib/color.node.js
function color(d) {
  return "\x1B[33m" + d + "\x1B[39m";
}

// node_modules/unist-util-visit-parents/lib/index.js
var empty = [];
var CONTINUE = true;
var EXIT = false;
var SKIP = "skip";
function visitParents(tree, test, visitor, reverse) {
  let check;
  if (typeof test === "function" && typeof visitor !== "function") {
    reverse = visitor;
    visitor = test;
  } else {
    check = test;
  }
  const is2 = convert(check);
  const step = reverse ? -1 : 1;
  factory(tree, void 0, [])();
  function factory(node, index, parents) {
    const value = (
      /** @type {Record<string, unknown>} */
      node && typeof node === "object" ? node : {}
    );
    if (typeof value.type === "string") {
      const name2 = (
        // `hast`
        typeof value.tagName === "string" ? value.tagName : (
          // `xast`
          typeof value.name === "string" ? value.name : void 0
        )
      );
      Object.defineProperty(visit2, "name", {
        value: "node (" + color(node.type + (name2 ? "<" + name2 + ">" : "")) + ")"
      });
    }
    return visit2;
    function visit2() {
      let result = empty;
      let subresult;
      let offset;
      let grandparents;
      if (!test || is2(node, index, parents[parents.length - 1] || void 0)) {
        result = toResult(visitor(node, parents));
        if (result[0] === EXIT) {
          return result;
        }
      }
      if ("children" in node && node.children) {
        const nodeAsParent = (
          /** @type {UnistParent} */
          node
        );
        if (nodeAsParent.children && result[0] !== SKIP) {
          offset = (reverse ? nodeAsParent.children.length : -1) + step;
          grandparents = parents.concat(nodeAsParent);
          while (offset > -1 && offset < nodeAsParent.children.length) {
            const child = nodeAsParent.children[offset];
            subresult = factory(child, offset, grandparents)();
            if (subresult[0] === EXIT) {
              return subresult;
            }
            offset = typeof subresult[1] === "number" ? subresult[1] : offset + step;
          }
        }
      }
      return result;
    }
  }
}
function toResult(value) {
  if (Array.isArray(value)) {
    return value;
  }
  if (typeof value === "number") {
    return [CONTINUE, value];
  }
  return value === null || value === void 0 ? empty : [value];
}

// node_modules/unist-util-visit/lib/index.js
function visit(tree, testOrVisitor, visitorOrReverse, maybeReverse) {
  let reverse;
  let test;
  let visitor;
  if (typeof testOrVisitor === "function" && typeof visitorOrReverse !== "function") {
    test = void 0;
    visitor = testOrVisitor;
    reverse = visitorOrReverse;
  } else {
    test = testOrVisitor;
    visitor = visitorOrReverse;
    reverse = maybeReverse;
  }
  visitParents(tree, test, overload, reverse);
  function overload(node, parents) {
    const parent = parents[parents.length - 1];
    const index = parent ? parent.children.indexOf(node) : void 0;
    return visitor(node, index, parent);
  }
}

// node_modules/retext-spell/lib/index.js
var emptyIgnore = [];
function retextSpell(options) {
  const settings = typeof options === "function" || options && "aff" in options && "dic" in options ? { dictionary: options } : options || {};
  const ignore = settings.ignore || emptyIgnore;
  const ignoreLiteral = typeof settings.ignoreLiteral === "boolean" ? settings.ignoreLiteral : true;
  const ignoreDigits = typeof settings.ignoreDigits === "boolean" ? settings.ignoreDigits : true;
  const max = settings.max || 30;
  const normalizeApostrophes = typeof settings.normalizeApostrophes === "boolean" ? (
    /* c8 ignore next -- this is now solved in `dictionary-en-gb` */
    settings.normalizeApostrophes
  ) : true;
  const personal = settings.personal;
  if (!settings.dictionary) {
    throw new TypeError("Missing `dictionary` in options");
  }
  const queue = [];
  let loadError;
  const state = {
    cache: /* @__PURE__ */ new Map(),
    checker: void 0,
    count: 0,
    ignore,
    ignoreLiteral,
    ignoreDigits,
    max,
    normalizeApostrophes
  };
  if (typeof settings.dictionary === "function") {
    settings.dictionary(onload);
  } else {
    onload(void 0, settings.dictionary);
  }
  return function(tree, file, next) {
    if (loadError) {
      next(loadError);
    } else if (state.checker) {
      all(tree, file, state);
      next();
    } else {
      queue.push([tree, file, state, next]);
    }
  };
  function onload(error, dictionary) {
    let index = -1;
    loadError = error;
    if (dictionary) {
      state.checker = (0, import_nspell.default)(dictionary);
      if (personal) {
        state.checker.personal(personal);
      }
    }
    while (++index < queue.length) {
      const [tree, file, state2, next] = queue[index];
      if (!error) {
        all(tree, file, state2);
      }
      next(error);
    }
    queue.length = 0;
  }
}
function all(tree, file, state) {
  visit(tree, "WordNode", function(node, position, parent) {
    if (!parent || position === void 0 || state.ignoreLiteral && isLiteral(parent, position)) {
      return;
    }
    let actual = toString(node);
    if (state.normalizeApostrophes) {
      actual = actual.replace(/’/g, "'");
    }
    if (irrelevant(actual)) {
      return;
    }
    let correct = state.checker.correct(actual);
    if (!correct && node.children.length > 1) {
      let index = -1;
      correct = true;
      while (++index < node.children.length) {
        const child = node.children[index];
        if (child.type !== "TextNode" || irrelevant(child.value)) {
          continue;
        }
        if (!state.checker.correct(child.value)) {
          correct = false;
        }
      }
    }
    if (!correct) {
      let suggestions = state.cache.get(actual);
      if (!suggestions) {
        if (state.count === state.max) {
          const message2 = file.info(
            "No longer generating suggestions to improve performance",
            {
              ancestors: [parent, node],
              place: node.position,
              ruleId: "overflow",
              source: "retext-spell"
            }
          );
          message2.note = "To keep on suggesting, increase `options.max`.";
        }
        suggestions = state.count < state.max ? (
          // @ts-expect-error: to do: type nspell.
          /** @type {Array<string>} */
          state.checker.suggest(actual)
        ) : [];
        state.count++;
        state.cache.set(actual, suggestions);
      }
      let extra = "";
      if (suggestions.length > 0) {
        extra = ", expected for example " + quotation([...suggestions], "`").join(", ");
      }
      const message = file.message(
        "Unexpected unknown word `" + actual + "`" + extra,
        {
          ancestors: [parent, node],
          place: node.position,
          ruleId: actual.toLowerCase().replace(/\W+/, "-"),
          source: "retext-spell"
        }
      );
      message.actual = actual;
      message.expected = [...suggestions];
      message.url = "https://github.com/retextjs/retext-spell#readme";
    }
  });
  function irrelevant(word) {
    return state.ignore.includes(word) || state.ignoreDigits && /^\d+$/.test(word) || state.ignoreDigits && /^\d{1,2}:\d{2}(?:[ap]\.?m\.?)?$/i.test(word);
  }
}

// js/retext-spell.mjs
var import_memoizee = __toESM(require_memoizee(), 1);
async function loadDictionary(locale) {
  const baseUrl = new URL(`https://unpkg.com/dictionary-${locale}@latest/`);
  const [aff, dic] = await Promise.all([
    fetch(new URL("index.aff", baseUrl)),
    fetch(new URL("index.dic", baseUrl))
  ]);
  if (!(aff.ok && dic.ok)) {
    throw new Error(`Couldn't load dictionary files from ${baseUrl}`);
  }
  return {
    aff: Buffer.from(await aff.arrayBuffer()),
    dic: Buffer.from(await dic.arrayBuffer())
  };
}
async function _createSpellPluginForLocale(locale, personalDictionary) {
  const dictionary = await loadDictionary(locale);
  return retextSpell({ dictionary, personal: personalDictionary.join("\n") });
}
var createSpellPluginForLocale = (0, import_memoizee.default)(_createSpellPluginForLocale, {
  promise: true
});
createSpellPluginForLocale("en");
var name = "retext-spell";
async function plugin(spellConfig) {
  const { dictionary: locale, "personal-dictionary": personalDictionary } = spellConfig;
  return await createSpellPluginForLocale(locale, personalDictionary);
}
// Annotate the CommonJS export names for ESM import in node:
0 && (module.exports = {
  name,
  plugin
});
/*! Bundled license information:

is-buffer/index.js:
  (*!
   * Determine if an object is a Buffer
   *
   * @author   Feross Aboukhadijeh <https://feross.org>
   * @license  MIT
   *)
*/

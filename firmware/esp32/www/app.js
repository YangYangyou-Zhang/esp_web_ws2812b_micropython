/* WS2812B console - vanilla JS, no external dependencies. */
(function () {
  'use strict';

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  var PRESETS = ['#FF3B30', '#FF6B35', '#FFB547', '#FFE066', '#3DDC97',
    '#22D3EE', '#4F8CFF', '#7C3AED', '#FF3D81', '#FFFFFF', '#FFD9A0',
    '#C8D8FF', '#FF8FAB', '#8AFFC1', '#B388FF', '#000000'];

  var QUICK = ['solid', 'breath', 'rainbow_flow', 'chase', 'comet', 'fire'];

  var I18N = {
    zh: {
      'brand.sub': '灯带控制台',
      'tab.control': '控制', 'tab.styles': '样式', 'tab.settings': '设置',
      'offline.banner': '设备未连接，正在重试…',
      'control.power': '电源', 'power.on': '已开启', 'power.off': '已关闭',
      'control.now': '当前样式', 'control.brightness': '亮度',
      'status.title': '状态', 'status.fps': '帧率', 'status.leds': '灯珠',
      'status.heap': '内存', 'status.uptime': '运行',
      'status.render': '渲染耗时', 'status.target': '目标帧率',
      'control.color': '颜色', 'control.saveColor': '收藏当前色',
      'control.pick': '打开取色器', 'control.presets': '预设颜色',
      'control.saved': '我的颜色', 'control.quick': '快捷效果',
      'control.more': '全部效果',
      'styles.effects': '内置效果', 'styles.effectsHint': '点击即可实时应用，参数可调',
      'styles.saveCurrent': '保存当前样式', 'styles.import': '导入 JSON',
      'styles.newPython': '新建 Python 样式', 'styles.saveAs': '存为我的样式',
      'styles.setBoot': '设为开机样式', 'styles.mine': '我的样式',
      'styles.mineHint': '保存在设备 flash 中，断电不丢失',
      'styles.empty': '还没有自定义样式', 'styles.noParams': '该样式没有可调参数',
      'styles.badgeBuiltin': 'JSON', 'styles.badgePy': 'PY',
      'settings.hardware': '硬件', 'settings.leds': 'LED 数量（每条）',
      'settings.pins': '数据引脚（逗号分隔）', 'settings.fps': '目标帧率',
      'settings.colorOrder': '颜色顺序',
      'common.applySave': '应用并保存',
      'settings.pinHint': '修改引脚或 AP 设置需要重启设备后生效。LED 数量会立即生效。',
      'settings.boot': '开机设置', 'settings.bootMode': '开机模式',
      'settings.modePreset': '使用指定样式', 'settings.modeOff': '保持关闭',
      'settings.bootStyle': '开机样式', 'settings.bootBright': '开机亮度',
      'settings.useCurrent': '用当前样式作为开机样式',
      'settings.network': '网络（AP）', 'settings.password': '密码',
      'settings.device': '设备信息', 'settings.logs': '查看日志',
      'settings.project': '项目地址', 'settings.author': '作者',
      'settings.authorName': '洋洋柚（B站/抖音 洋洋柚Y）',
      'settings.license': '协议',
      'settings.nonCommercial': '禁止商用 NonCommercial',
      'settings.linksHint': '链接需联网访问，也可长按复制',
      'settings.reboot': '重启设备', 'common.save': '保存',
      'common.cancel': '取消', 'common.confirm': '确定', 'common.close': '关闭',
      'common.delete': '删除', 'common.apply': '应用', 'common.edit': '编辑',
      'common.export': '导出', 'common.boot': '开机', 'common.source': '源码',
      'picker.title': '选择颜色',
      'toast.saved': '已保存', 'toast.applied': '已应用', 'toast.deleted': '已删除',
      'toast.offline': '设备已断开', 'toast.online': '设备已连接',
      'toast.imported': '样式已导入', 'toast.invalid': '文件格式不正确',
      'toast.rebootRequired': '已保存，重启后生效', 'toast.colorSaved': '颜色已收藏',
      'toast.pySaved': 'Python 样式已保存', 'toast.reboot': '设备正在重启…',
      'toast.error': '操作失败', 'toast.invalidValue': '数值不正确',
      'toast.saveOnlyBuiltin': '只能把内置效果另存为样式',
      'toast.noSelection': '请先选择一个效果',
      'dlg.saveStyleTitle': '保存为我的样式', 'dlg.styleName': '样式名称',
      'dlg.importTitle': '导入样式', 'dlg.importHint': '选择从本设备导出的 JSON 样式文件，或包含完整样式定义的 JSON 文件。',
      'dlg.editTitle': '编辑样式 JSON', 'dlg.pyTitle': '新建 Python 样式',
      'dlg.pyName': '样式名称', 'dlg.pyParams': '参数定义（JSON 数组，可留空）',
      'dlg.pyCode': 'Python 源码', 'dlg.pyHint': 'render(t, n, params, out, h) 每帧调用，请保持简短。死循环会让设备卡死。',
      'dlg.rebootTitle': '确认重启设备？', 'dlg.rebootBody': '设备将断开连接，约 3 秒后重新启动。',
      'dlg.deleteTitle': '确认删除样式？', 'dlg.deleteBody': '删除后无法恢复。',
      'dlg.logsTitle': '设备日志', 'dlg.nameRequired': '请填写名称',
      'dlg.sourceTitle': '编辑 Python 源码', 'dlg.pickPy': '从文件载入 .py'
    },
    en: {
      'brand.sub': 'LED strip console',
      'tab.control': 'Control', 'tab.styles': 'Styles', 'tab.settings': 'Settings',
      'offline.banner': 'Device offline, retrying…',
      'control.power': 'Power', 'power.on': 'On', 'power.off': 'Off',
      'control.now': 'Current style', 'control.brightness': 'Brightness',
      'status.title': 'Status', 'status.fps': 'FPS', 'status.leds': 'LEDs',
      'status.heap': 'Heap', 'status.uptime': 'Uptime',
      'status.render': 'Render', 'status.target': 'Target FPS',
      'control.color': 'Colour', 'control.saveColor': 'Save colour',
      'control.pick': 'Open picker', 'control.presets': 'Preset colours',
      'control.saved': 'My colours', 'control.quick': 'Quick effects',
      'control.more': 'All effects',
      'styles.effects': 'Built-in effects', 'styles.effectsHint': 'Tap to apply instantly, tweak parameters below',
      'styles.saveCurrent': 'Save current style', 'styles.import': 'Import JSON',
      'styles.newPython': 'New Python style', 'styles.saveAs': 'Save as my style',
      'styles.setBoot': 'Set as boot style', 'styles.mine': 'My styles',
      'styles.mineHint': 'Stored on the device, survives power cycles',
      'styles.empty': 'No custom styles yet', 'styles.noParams': 'This style has no adjustable parameters',
      'styles.badgeBuiltin': 'JSON', 'styles.badgePy': 'PY',
      'settings.hardware': 'Hardware', 'settings.leds': 'LEDs per strip',
      'settings.pins': 'Data pins (comma separated)', 'settings.fps': 'Target FPS',
      'settings.colorOrder': 'Colour order',
      'common.applySave': 'Apply & save',
      'settings.pinHint': 'Pin or AP changes need a reboot. LED count applies immediately.',
      'settings.boot': 'Boot', 'settings.bootMode': 'Boot mode',
      'settings.modePreset': 'Use a style', 'settings.modeOff': 'Stay off',
      'settings.bootStyle': 'Boot style', 'settings.bootBright': 'Boot brightness',
      'settings.useCurrent': 'Use current style at boot',
      'settings.network': 'Network (AP)', 'settings.password': 'Password',
      'settings.device': 'Device', 'settings.logs': 'View logs',
      'settings.project': 'Project', 'settings.author': 'Author',
      'settings.authorName': 'YangYangyou (Bilibili/Douyin: 洋洋柚Y)',
      'settings.license': 'License',
      'settings.nonCommercial': 'NonCommercial',
      'settings.linksHint': 'Links need internet access; long-press to copy',
      'settings.reboot': 'Reboot', 'common.save': 'Save',
      'common.cancel': 'Cancel', 'common.confirm': 'OK', 'common.close': 'Close',
      'common.delete': 'Delete', 'common.apply': 'Apply', 'common.edit': 'Edit',
      'common.export': 'Export', 'common.boot': 'Boot', 'common.source': 'Source',
      'picker.title': 'Pick a colour',
      'toast.saved': 'Saved', 'toast.applied': 'Applied', 'toast.deleted': 'Deleted',
      'toast.offline': 'Device disconnected', 'toast.online': 'Device connected',
      'toast.imported': 'Style imported', 'toast.invalid': 'Invalid file',
      'toast.rebootRequired': 'Saved, reboot to apply', 'toast.colorSaved': 'Colour saved',
      'toast.pySaved': 'Python style saved', 'toast.reboot': 'Rebooting…',
      'toast.error': 'Failed', 'toast.invalidValue': 'Invalid value',
      'toast.saveOnlyBuiltin': 'Only built-in effects can be saved as styles',
      'toast.noSelection': 'Select an effect first',
      'dlg.saveStyleTitle': 'Save as my style', 'dlg.styleName': 'Style name',
      'dlg.importTitle': 'Import style', 'dlg.importHint': 'Choose a JSON style file exported from this device.',
      'dlg.editTitle': 'Edit style JSON', 'dlg.pyTitle': 'New Python style',
      'dlg.pyName': 'Style name', 'dlg.pyParams': 'Parameter definitions (JSON array, optional)',
      'dlg.pyCode': 'Python source', 'dlg.pyHint': 'render(t, n, params, out, h) runs every frame. Keep it short; an infinite loop will freeze the device.',
      'dlg.rebootTitle': 'Reboot device?', 'dlg.rebootBody': 'The device will disconnect and be back in a few seconds.',
      'dlg.deleteTitle': 'Delete this style?', 'dlg.deleteBody': 'This cannot be undone.',
      'dlg.logsTitle': 'Device logs', 'dlg.nameRequired': 'Name is required',
      'dlg.sourceTitle': 'Edit Python source', 'dlg.pickPy': 'Load a .py file'
    }
  };

  var S = {
    lang: 'zh', theme: 'light', online: null,
    device: {}, settings: null, runtime: {}, effects: [], styles: [], colors: [],
    selectedId: null, params: {}, color: '#FF6600',
    pickerTarget: null, picker: { h: 20, s: 1, v: 1 },
    lastLocal: 0, applyTimer: null, pollTimer: null, toastTimer: null,
    settingsFilled: false
  };

  function t(key) {
    var d = I18N[S.lang] || I18N.zh;
    return d[key] !== undefined ? d[key] : (I18N.en[key] !== undefined ? I18N.en[key] : key);
  }

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function esc(v) {
    return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function clamp(v, lo, hi) { return v < lo ? lo : (v > hi ? hi : v); }

  function debounce(fn, ms) {
    var timer = null;
    return function () {
      var args = arguments;
      clearTimeout(timer);
      timer = setTimeout(function () { fn.apply(null, args); }, ms);
    };
  }

  function markLocal() { S.lastLocal = Date.now(); }

  function toast(msg, kind) {
    var box = $('#toast');
    box.textContent = msg;
    box.className = 'toast show' + (kind === 'error' ? ' error' : '');
    clearTimeout(S.toastTimer);
    S.toastTimer = setTimeout(function () { box.className = 'toast'; }, 2600);
  }

  function api(path, method, body) {
    var opt = { method: method || 'GET', headers: {} };
    if (body !== undefined) {
      opt.headers['Content-Type'] = 'application/json';
      opt.body = JSON.stringify(body);
    }
    return fetch(path, opt).then(function (res) {
      return res.text().then(function (text) {
        var data = null;
        try { data = text ? JSON.parse(text) : null; } catch (e) { data = null; }
        if (!res.ok || (data && data.ok === false)) {
          throw new Error((data && data.error) || ('HTTP ' + res.status));
        }
        return data;
      });
    });
  }

  function apiSource(path) {
    return fetch(path).then(function (res) {
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return res.text();
    });
  }

  function apiRaw(path, method, text) {
    return fetch(path, {
      method: method,
      headers: { 'Content-Type': 'text/plain; charset=utf-8' },
      body: text
    }).then(function (res) {
      return res.text().then(function (body) {
        var data = null;
        try { data = body ? JSON.parse(body) : null; } catch (e) { data = null; }
        if (!res.ok || (data && data.ok === false)) {
          throw new Error((data && data.error) || ('HTTP ' + res.status));
        }
        return data;
      });
    });
  }

  /* ---------------- i18n / theme ---------------- */

  function applyI18n() {
    $$('[data-i18n]').forEach(function (n) { n.textContent = t(n.getAttribute('data-i18n')); });
    $$('[data-i18n-ph]').forEach(function (n) { n.setAttribute('placeholder', t(n.getAttribute('data-i18n-ph'))); });
    document.documentElement.lang = S.lang;
    $('#langBtn').textContent = S.lang === 'zh' ? 'EN' : '中';
  }

  function setLang(lang) {
    S.lang = (lang === 'en') ? 'en' : 'zh';
    localStorage.setItem('ws.lang', S.lang);
    applyI18n();
    renderEffects();
    renderQuickEffects();
    renderStyles();
    renderParamPanel();
    renderBootStyleOptions(S.settings ? S.settings.boot.style : null);
    renderRuntime();
    renderColorSwatches();
    if (S.settings) fillSettings(S.settings);
  }

  function applyTheme(theme) {
    S.theme = theme === 'light' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', S.theme);
    localStorage.setItem('ws.theme', S.theme);
  }

  /* ---------------- colour helpers ---------------- */

  function hexToRgb(hex) {
    var h = String(hex || '').replace('#', '');
    if (!/^[0-9a-fA-F]{6}$/.test(h)) return [0, 0, 0];
    return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
  }

  function rgbToHex(r, g, b) {
    function p(x) {
      x = clamp(Math.round(x), 0, 255).toString(16);
      return x.length < 2 ? '0' + x : x;
    }
    return ('#' + p(r) + p(g) + p(b)).toUpperCase();
  }

  function rgbToHsv(r, g, b) {
    r /= 255; g /= 255; b /= 255;
    var max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min;
    var h = 0;
    if (d !== 0) {
      if (max === r) h = 60 * (((g - b) / d) % 6);
      else if (max === g) h = 60 * ((b - r) / d + 2);
      else h = 60 * ((r - g) / d + 4);
    }
    if (h < 0) h += 360;
    return [h, max === 0 ? 0 : d / max, max];
  }

  function hsvToRgb(h, s, v) {
    var c = v * s, x = c * (1 - Math.abs(((h / 60) % 2) - 1)), m = v - c;
    var r = 0, g = 0, b = 0;
    if (h < 60) { r = c; g = x; }
    else if (h < 120) { r = x; g = c; }
    else if (h < 180) { g = c; b = x; }
    else if (h < 240) { g = x; b = c; }
    else if (h < 300) { r = x; b = c; }
    else { r = c; b = x; }
    return [(r + m) * 255, (g + m) * 255, (b + m) * 255];
  }

  function pickerHex() {
    var rgb = hsvToRgb(S.picker.h, S.picker.s, S.picker.v);
    return rgbToHex(rgb[0], rgb[1], rgb[2]);
  }

  function setCurrentColor(hex) {
    S.color = hex;
    localStorage.setItem('ws.color', hex);
    $('#currentSwatch').style.background = hex;
    $('#colorHex').textContent = hex;
  }

  /* ---------------- runtime UI ---------------- */

  function setOnline(on) {
    var prev = S.online;
    S.online = on;
    $('#connDot').className = 'conn-dot' + (on ? ' online' : '');
    $('#offlineBanner').classList.toggle('hidden', on);
    if (prev !== null && prev !== on) {
      toast(on ? t('toast.online') : t('toast.offline'), on ? '' : 'error');
    }
  }

  function fmtUptime(sec) {
    sec = Math.max(0, Math.floor(sec || 0));
    var h = Math.floor(sec / 3600), m = Math.floor((sec % 3600) / 60), s = sec % 60;
    function p(n) { return n < 10 ? '0' + n : '' + n; }
    return h > 0 ? (h + ':' + p(m) + ':' + p(s)) : (p(m) + ':' + p(s));
  }

  function renderRuntime() {
    var rt = S.runtime || {};
    var on = !!rt.power;
    $('#powerBtn').classList.toggle('on', on);
    $('#powerBtn').setAttribute('aria-pressed', on ? 'true' : 'false');
    $('#powerState').textContent = on ? t('power.on') : t('power.off');
    $('#nowStyle').textContent = rt.style_name || '--';
    if (document.activeElement !== $('#brightness')) {
      $('#brightness').value = rt.brightness !== undefined ? rt.brightness : 128;
    }
    $('#brightVal').textContent = (rt.brightness !== undefined ? rt.brightness : '--');
    $('#statFps').textContent = (rt.fps !== undefined ? rt.fps : '--');
    $('#statLeds').textContent = (rt.leds !== undefined ? rt.leds : '--');
    $('#statHeap').textContent = rt.heap ? (Math.round(rt.heap / 1024) + ' KB') : '--';
    $('#statUptime').textContent = fmtUptime(rt.uptime);
    $('#statRender').textContent = (rt.render_ms !== undefined ? rt.render_ms + ' ms' : '--');
    $('#statTarget').textContent = (rt.fps_target !== undefined ? rt.fps_target : '--');
    renderDeviceInfo();
  }

  function renderDeviceInfo() {
    var d = S.device || {}, rt = S.runtime || {};
    var rows = [
      ['Platform', d.platform || '--'],
      ['Machine', d.machine || '--'],
      ['SSID', d.ssid || '--'],
      ['IP', d.ip || '--'],
      ['Chip ID', d.chip_id || '--'],
      ['Firmware', d.version || '--'],
      ['Pins', (rt.pins || []).join(', ') || '--'],
      ['Render', (rt.render_ms !== undefined ? rt.render_ms + ' ms' : '--')]
    ];
    var html = '';
    rows.forEach(function (r) {
      html += '<dt>' + esc(r[0]) + '</dt><dd>' + esc(r[1]) + '</dd>';
    });
    $('#deviceInfo').innerHTML = html;
  }

  /* ---------------- swatches ---------------- */

  function swatchButton(hex, onClick, selected) {
    var b = el('button', 'swatch-btn' + (selected ? ' selected' : ''));
    b.style.background = hex;
    b.title = hex;
    b.setAttribute('aria-label', hex);
    b.addEventListener('click', function () { onClick(hex); });
    return b;
  }

  function renderColorSwatches() {
    var p = $('#presetSwatches');
    p.innerHTML = '';
    PRESETS.forEach(function (c) {
      p.appendChild(swatchButton(c, function (hex) {
        setCurrentColor(hex);
        markLocal();
        S.selectedId = 'builtin:solid';
        S.params = { color: hex };
        renderSelection();
        applyNow();
      }, c === S.color));
    });

    var u = $('#userSwatches');
    u.innerHTML = '';
    if (!S.colors.length) {
      u.appendChild(el('span', 'swatch-empty', S.lang === 'zh' ? '还没有收藏颜色' : 'No saved colours'));
    } else {
      S.colors.forEach(function (c) {
        u.appendChild(swatchButton(c, function (hex) {
          setCurrentColor(hex);
          markLocal();
          S.selectedId = 'builtin:solid';
          S.params = { color: hex };
          renderSelection();
          applyNow();
        }, c === S.color));
      });
    }

    var ps = $('#pickSwatches');
    if (ps) {
      ps.innerHTML = '';
      PRESETS.forEach(function (c) {
        ps.appendChild(swatchButton(c, function (hex) { setPickerColor(hex); }, false));
      });
    }
    var pu = $('#pickUserSwatches');
    if (pu) {
      pu.innerHTML = '';
      S.colors.forEach(function (c) {
        pu.appendChild(swatchButton(c, function (hex) { setPickerColor(hex); }, false));
      });
    }
  }

  /* ---------------- effects ---------------- */

  function effectLabel(fx) { return (fx.name && (fx.name[S.lang] || fx.name.en)) || fx.id; }
  function effectDesc(fx) { return (fx.desc && (fx.desc[S.lang] || fx.desc.en)) || ''; }
  function paramLabel(d) { return (d.label && (d.label[S.lang] || d.label.en)) || d.key; }

  function defaultsFor(defs) {
    var out = {};
    (defs || []).forEach(function (d) {
      var v = d.default;
      if (v === undefined) {
        if (d.type === 'int') v = d.min || 0;
        else if (d.type === 'bool') v = false;
        else if (d.type === 'color') v = '#FFFFFF';
        else if (d.type === 'colors') v = ['#FFFFFF'];
        else if (d.type === 'enum') v = (d.options && d.options[0] && d.options[0].value);
      }
      out[d.key] = (d.type === 'colors' && Array.isArray(v)) ? v.slice() : v;
    });
    return out;
  }

  function renderEffects() {
    var grid = $('#effectGrid');
    grid.innerHTML = '';
    S.effects.forEach(function (fx) {
      var card = el('button', 'effect-card');
      card.setAttribute('data-id', fx.id);
      card.innerHTML =
        '<div class="fx-thumb anim-' + esc(fx.anim || 'static') + '"></div>' +
        '<div class="fx-meta"><strong>' + esc(effectLabel(fx)) + '</strong>' +
        '<span>' + esc(effectDesc(fx) || fx.id) + '</span></div>';
      if (S.selectedId === 'builtin:' + fx.id) card.classList.add('selected');
      card.addEventListener('click', function () { selectEffect(fx.id); });
      grid.appendChild(card);
    });
  }

  function renderQuickEffects() {
    var box = $('#quickEffects');
    box.innerHTML = '';
    QUICK.forEach(function (id) {
      var fx = S.effects.filter(function (e) { return e.id === id; })[0];
      if (!fx) return;
      var b = el('button', 'chip', effectLabel(fx));
      b.setAttribute('data-id', id);
      if (S.selectedId === 'builtin:' + id) b.classList.add('active');
      b.addEventListener('click', function () { selectEffect(id); });
      box.appendChild(b);
    });
  }

  function openParamSheet() {
    var page = document.getElementById('page-styles');
    if (!page.classList.contains('active')) return;
    var panel = $('#paramPanel');
    if (window.innerWidth < 760) {
      panel.classList.add('open');
    } else if (panel.scrollIntoView) {
      panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  function selectEffect(id) {
    var fx = S.effects.filter(function (e) { return e.id === id; })[0];
    if (!fx) return;
    S.selectedId = 'builtin:' + id;
    S.params = defaultsFor(fx.params);
    if (id === 'solid') S.params.color = S.color;
    markLocal();
    renderSelection();
    openParamSheet();
    applyNow();
  }

  function renderSelection() {
    $$('.effect-card').forEach(function (c) {
      c.classList.toggle('selected', 'builtin:' + c.getAttribute('data-id') === S.selectedId);
    });
    $$('#quickEffects .chip').forEach(function (c) {
      var id = c.getAttribute('data-id');
      c.classList.toggle('active', !!id && 'builtin:' + id === S.selectedId);
    });
    renderParamPanel();
  }

  function selectedInfo() {
    if (!S.selectedId) return null;
    if (S.selectedId.indexOf('builtin:') === 0) {
      var id = S.selectedId.slice(8);
      var fx = S.effects.filter(function (e) { return e.id === id; })[0];
      if (!fx) return null;
      return { title: effectLabel(fx), defs: fx.params || [] };
    }
    var st = S.styles.filter(function (s) { return s.id === S.selectedId; })[0];
    if (!st) return { title: S.selectedId, defs: [] };
    return { title: st.name, defs: st.param_defs || [] };
  }

  function ensureParam(d) {
    var v = S.params[d.key];
    if (v === undefined || v === null) {
      v = (d.default !== undefined) ? d.default : undefined;
      if (v === undefined) {
        if (d.type === 'int') v = d.min || 0;
        else if (d.type === 'bool') v = false;
        else if (d.type === 'color') v = '#FFFFFF';
        else if (d.type === 'colors') v = ['#FFFFFF'];
        else if (d.type === 'enum') v = d.options && d.options[0] ? d.options[0].value : '';
      }
      S.params[d.key] = (d.type === 'colors' && Array.isArray(v)) ? v.slice() : v;
    }
    return S.params[d.key];
  }

  function renderParamPanel() {
    var panel = $('#paramPanel');
    var info = selectedInfo();
    if (!info) { panel.classList.add('hidden'); return; }
    panel.classList.remove('hidden');
    $('#paramTitle').textContent = info.title;
    var box = $('#paramControls');
    box.innerHTML = '';
    if (!info.defs.length) {
      box.appendChild(el('p', 'muted', t('styles.noParams')));
      return;
    }
    info.defs.forEach(function (d) { box.appendChild(buildParamRow(d)); });
  }

  function buildParamRow(d) {
    var row = el('div', 'param-row');
    row.appendChild(el('label', '', paramLabel(d)));

    if (d.type === 'int') {
      var v = ensureParam(d);
      var wrap = el('div', 'param-inline');
      var inp = el('input', 'range');
      inp.type = 'range';
      inp.min = d.min !== undefined ? d.min : 0;
      inp.max = d.max !== undefined ? d.max : 100;
      inp.step = 1;
      inp.value = v;
      var out = el('span', 'param-value', String(v));
      inp.addEventListener('input', function () {
        S.params[d.key] = parseInt(inp.value, 10);
        out.textContent = inp.value;
        markLocal();
        scheduleApply();
      });
      wrap.appendChild(inp);
      wrap.appendChild(out);
      row.appendChild(wrap);
      return row;
    }

    if (d.type === 'bool') {
      var cb = el('label', 'switch');
      var input = document.createElement('input');
      input.type = 'checkbox';
      input.checked = !!ensureParam(d);
      input.addEventListener('change', function () {
        S.params[d.key] = input.checked;
        markLocal();
        scheduleApply();
      });
      cb.appendChild(input);
      cb.appendChild(document.createElement('span'));
      row.appendChild(cb);
      return row;
    }

    if (d.type === 'enum') {
      var sel = document.createElement('select');
      (d.options || []).forEach(function (o) {
        var op = document.createElement('option');
        op.value = o.value;
        op.textContent = (o.label && (o.label[S.lang] || o.label.en)) || o.value;
        sel.appendChild(op);
      });
      sel.value = ensureParam(d);
      sel.addEventListener('change', function () {
        S.params[d.key] = sel.value;
        markLocal();
        scheduleApply();
      });
      row.appendChild(sel);
      return row;
    }

    if (d.type === 'color') {
      var val = ensureParam(d);
      var btn = el('button', 'param-color-btn');
      btn.innerHTML = '<span class="swatch" style="background:' + esc(val) + '"></span>' +
        '<span>' + esc(val) + '</span>';
      btn.addEventListener('click', function () {
        openPicker({ kind: 'param', key: d.key }, val);
      });
      row.appendChild(btn);
      return row;
    }

    if (d.type === 'colors') {
      var arr = ensureParam(d);
      if (!Array.isArray(arr)) arr = ['#FFFFFF'];
      S.params[d.key] = arr;
      var chips = el('div', 'color-chips');
      arr.forEach(function (c, idx) {
        var chip = el('button', 'color-chip');
        chip.style.background = c;
        chip.title = c;
        chip.addEventListener('click', function (e) {
          e.stopPropagation();
          openPicker({ kind: 'paramColor', key: d.key, index: idx }, c);
        });
        if (arr.length > 1) {
          var x = el('span', 'chip-x', '×');
          x.addEventListener('click', function (e) {
            e.stopPropagation();
            arr.splice(idx, 1);
            markLocal();
            renderParamPanel();
            scheduleApply();
          });
          chip.appendChild(x);
        }
        chips.appendChild(chip);
      });
      var add = el('button', 'chip-add', '+');
      add.title = S.lang === 'zh' ? '添加颜色' : 'Add colour';
      add.addEventListener('click', function () {
        if (arr.length >= 8) return;
        arr.push('#FFFFFF');
        markLocal();
        renderParamPanel();
        scheduleApply();
      });
      chips.appendChild(add);
      row.appendChild(chips);
      return row;
    }

    row.appendChild(el('span', '', ''));
    return row;
  }

  function scheduleApply() {
    clearTimeout(S.applyTimer);
    S.applyTimer = setTimeout(applyNow, 180);
  }

  function applyNow() {
    if (!S.selectedId) return;
    return api('/api/apply', 'POST', { style_id: S.selectedId, params: S.params })
      .then(function (d) {
        if (d.runtime) { S.runtime = d.runtime; renderRuntime(); }
        if (S.selectedId === 'builtin:solid' && S.params.color) setCurrentColor(S.params.color);
      })
      .catch(function (e) { toast(e.message, 'error'); });
  }

  /* ---------------- styles list ---------------- */

  function renderStyles() {
    var list = $('#styleList');
    list.innerHTML = '';
    if (!S.styles.length) {
      list.appendChild(el('div', 'empty', t('styles.empty')));
      return;
    }
    S.styles.forEach(function (st) {
      var item = el('div', 'style-item');
      var badge = st.type === 'python' ? 'PY' : 'JSON';
      var sub = st.type === 'python' ? ('python: ' + st.module) : ('effect: ' + st.effect);
      item.innerHTML =
        '<div class="si-main"><div class="si-name">' + esc(st.name) + '</div>' +
        '<div class="si-sub">' + esc(sub) + '</div></div>' +
        '<span class="badge' + (st.type === 'python' ? ' py' : '') + '">' + badge + '</span>' +
        '<div class="si-actions">' +
        '<button class="mini-btn" data-act="apply">' + esc(t('common.apply')) + '</button>' +
        '<button class="mini-btn" data-act="boot">' + esc(t('common.boot')) + '</button>' +
        '<button class="mini-btn" data-act="export">' + esc(t('common.export')) + '</button>' +
        (st.type === 'python' ? '<button class="mini-btn" data-act="source">' + esc(t('common.source')) + '</button>' : '') +
        '<button class="mini-btn" data-act="edit">' + esc(t('common.edit')) + '</button>' +
        '<button class="mini-btn danger" data-act="delete">' + esc(t('common.delete')) + '</button>' +
        '</div>';
      item.querySelector('[data-act="apply"]').addEventListener('click', function () { applyStyleFile(st.id); });
      item.querySelector('[data-act="boot"]').addEventListener('click', function () { bootStyleFile(st); });
      item.querySelector('[data-act="export"]').addEventListener('click', function () { exportStyle(st.id); });
      item.querySelector('[data-act="edit"]').addEventListener('click', function () { editStyle(st); });
      var srcBtn = item.querySelector('[data-act="source"]');
      if (srcBtn) srcBtn.addEventListener('click', function () { editSource(st); });
      item.querySelector('[data-act="delete"]').addEventListener('click', function () { deleteStyle(st); });
      list.appendChild(item);
    });
  }

  function applyStyleFile(id) {
    var st = S.styles.filter(function (s) { return s.id === id; })[0];
    if (!st) return;
    S.selectedId = id;
    S.params = JSON.parse(JSON.stringify(st.params || {}));
    markLocal();
    renderSelection();
    openParamSheet();
    applyNow();
  }

  function bootStyleFile(st) {
    api('/api/save-boot', 'POST', {
      style_id: st.id, params: st.params || {},
      brightness: S.runtime.brightness !== undefined ? S.runtime.brightness : 128,
      power: true
    }).then(function () {
      toast(t('toast.saved'));
      return refreshState(true);
    }).catch(function (e) { toast(e.message, 'error'); });
  }

  function exportStyle(id) {
    api('/api/styles/' + encodeURIComponent(id)).then(function (d) {
      var text = JSON.stringify(d.style, null, 2);
      var blob = new Blob([text], { type: 'application/json' });
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = id + '.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(function () { URL.revokeObjectURL(a.href); }, 1500);
    }).catch(function (e) { toast(e.message, 'error'); });
  }

  function editStyle(st) {
    api('/api/styles/' + encodeURIComponent(st.id)).then(function (d) {
      openDialog({
        title: t('dlg.editTitle'),
        body: '<label>' + esc(st.id + '.json') + '<textarea id="dlgJson" spellcheck="false"></textarea></label>',
        actions: [
          { label: t('common.cancel'), onClick: function (close) { close(); } },
          {
            label: t('common.save'), cls: 'primary-btn', onClick: function (close) {
              var text = $('#dlgJson').value;
              var obj;
              try { obj = JSON.parse(text); } catch (e) { toast(t('toast.invalid'), 'error'); return; }
              api('/api/styles/' + encodeURIComponent(st.id), 'PUT', obj).then(function () {
                close();
                toast(t('toast.saved'));
                return loadStyles();
              }).then(renderStyles).catch(function (e) { toast(e.message, 'error'); });
            }
          }
        ],
        after: function () {
          $('#dlgJson').value = JSON.stringify(d.style, null, 2);
        }
      });
    }).catch(function (e) { toast(e.message, 'error'); });
  }

  function editSource(st) {
    apiSource('/api/styles/' + encodeURIComponent(st.id) + '.py').then(function (src) {
      openDialog({
        title: t('dlg.sourceTitle') + ' · ' + st.id,
        body: '<label>' + esc(st.id + '.py') +
          '<textarea id="dlgSrc" spellcheck="false"></textarea></label>',
        actions: [
          { label: t('common.cancel'), onClick: function (close) { close(); } },
          {
            label: t('common.save'), cls: 'primary-btn', onClick: function (close) {
              apiRaw('/api/styles/' + encodeURIComponent(st.id) + '.py', 'PUT', $('#dlgSrc').value)
                .then(function () {
                  close();
                  toast(t('toast.pySaved'));
                })
                .catch(function (e) { toast(e.message, 'error'); });
            }
          }
        ],
        after: function () { $('#dlgSrc').value = src; }
      });
    }).catch(function (e) { toast(e.message, 'error'); });
  }

  function deleteStyle(st) {
    openDialog({
      title: t('dlg.deleteTitle'),
      body: '<p>' + esc(st.name) + '</p><p class="muted">' + esc(t('dlg.deleteBody')) + '</p>',
      actions: [
        { label: t('common.cancel'), onClick: function (close) { close(); } },
        {
          label: t('common.delete'), cls: 'danger-btn', onClick: function (close) {
            api('/api/styles/' + encodeURIComponent(st.id), 'DELETE').then(function () {
              close();
              toast(t('toast.deleted'));
              if (S.selectedId === st.id) S.selectedId = null;
              return loadStyles();
            }).then(function () {
              renderStyles();
              renderSelection();
            }).catch(function (e) { toast(e.message, 'error'); });
          }
        }
      ]
    });
  }

  function slugify(name) {
    var s = String(name || '').toLowerCase().replace(/[^a-z0-9_-]+/g, '-')
      .replace(/^-+|-+$/g, '').slice(0, 22);
    return s || 'style';
  }

  function uniqueId(base) {
    var id = base, n = 2;
    while (S.styles.some(function (s) { return s.id === id; }) ||
      S.effects.some(function (e) { return 'builtin:' + e.id === id; })) {
      id = base + '-' + n;
      n++;
    }
    return id;
  }

  function saveCurrentStyle() {
    if (!S.selectedId) { toast(t('toast.noSelection'), 'error'); return; }
    if (S.selectedId.indexOf('builtin:') !== 0) { toast(t('toast.saveOnlyBuiltin'), 'error'); return; }
    openDialog({
      title: t('dlg.saveStyleTitle'),
      body: '<label>' + esc(t('dlg.styleName')) + '<input id="dlgName" type="text" maxlength="32"></label>',
      actions: [
        { label: t('common.cancel'), onClick: function (close) { close(); } },
        {
          label: t('common.save'), cls: 'primary-btn', onClick: function (close) {
            var name = $('#dlgName').value.trim();
            if (!name) { toast(t('dlg.nameRequired'), 'error'); return; }
            var id = uniqueId(slugify(name));
            var payload = {
              schema: 1, name: name, type: 'builtin',
              effect: S.selectedId.slice(8), params: S.params
            };
            api('/api/styles/' + id, 'PUT', payload).then(function () {
              close();
              toast(t('toast.saved'));
              return loadStyles();
            }).then(function () {
              renderStyles();
              renderBootStyleOptions(S.settings ? S.settings.boot.style : null);
            }).catch(function (e) { toast(e.message, 'error'); });
          }
        }
      ],
      after: function () {
        var fx = S.effects.filter(function (e) { return 'builtin:' + e.id === S.selectedId; })[0];
        $('#dlgName').value = fx ? effectLabel(fx) : '';
      }
    });
  }

  function importStyleFile(file) {
    file.text().then(function (text) {
      var obj;
      try { obj = JSON.parse(text); } catch (e) { toast(t('toast.invalid'), 'error'); return; }
      var base = slugify(obj.name || file.name.replace(/\.json$/i, ''));
      var id = uniqueId(base);
      obj.schema = 1;
      if (!obj.name) obj.name = id;
      if (obj.type === 'python' && !obj.module) obj.module = id;
      api('/api/styles/' + id, 'PUT', obj).then(function () {
        toast(t('toast.imported'));
        return loadStyles();
      }).then(function () {
        renderStyles();
        renderBootStyleOptions(S.settings ? S.settings.boot.style : null);
      }).catch(function (e) { toast(e.message, 'error'); });
    });
  }

  function newPythonStyle() {
    var sample = 'NAME = "My Effect"\nDEFAULTS = {"speed": 40, "color": "#FF3300"}\n\n' +
      'def render(t, n, params, out, h):\n' +
      '    head = int(t * params["speed"]) % n\n' +
      '    c = h.rgb(params["color"])\n' +
      '    for i in range(n):\n' +
      '        d = (head - i) % n\n' +
      '        v = 1.0 - d / 12.0\n' +
      '        if v < 0:\n' +
      '            v = 0.0\n' +
      '        out[i][0] = int(c[0] * v)\n' +
      '        out[i][1] = int(c[1] * v)\n' +
      '        out[i][2] = int(c[2] * v)\n';
    var sampleDefs = JSON.stringify([
      { key: 'speed', type: 'int', min: 1, max: 100, default: 40, label: { zh: '速度', en: 'Speed' } },
      { key: 'color', type: 'color', default: '#FF3300', label: { zh: '颜色', en: 'Colour' } }
    ], null, 2);
    openDialog({
      title: t('dlg.pyTitle'),
      body:
        '<label>' + esc(t('dlg.pyName')) + '<input id="dlgName" type="text" maxlength="32"></label>' +
        '<label>' + esc(t('dlg.pyParams')) + '<textarea id="dlgDefs" spellcheck="false"></textarea></label>' +
        '<label>' + esc(t('dlg.pickPy')) + '<input id="dlgPyFile" type="file" accept=".py"></label>' +
        '<label>' + esc(t('dlg.pyCode')) + '<textarea id="dlgCode" spellcheck="false"></textarea></label>' +
        '<p class="muted">' + esc(t('dlg.pyHint')) + '</p>',
      actions: [
        { label: t('common.cancel'), onClick: function (close) { close(); } },
        {
          label: t('common.save'), cls: 'primary-btn', onClick: function (close) {
            var name = $('#dlgName').value.trim();
            if (!name) { toast(t('dlg.nameRequired'), 'error'); return; }
            var defsText = $('#dlgDefs').value.trim();
            var defs = [];
            if (defsText) {
              try { defs = JSON.parse(defsText); } catch (e) { toast(t('toast.invalid'), 'error'); return; }
              if (!Array.isArray(defs)) { toast(t('toast.invalid'), 'error'); return; }
            }
            var code = $('#dlgCode').value;
            var id = uniqueId(slugify(name));
            var sidecar = {
              schema: 1, name: name, type: 'python', module: id,
              params: {}, param_defs: defs
            };
            api('/api/styles/' + id, 'PUT', sidecar)
              .then(function () { return apiRaw('/api/styles/' + id + '.py', 'PUT', code); })
              .then(function () {
                close();
                toast(t('toast.pySaved'));
                return loadStyles();
              }).then(function () {
                renderStyles();
                renderBootStyleOptions(S.settings ? S.settings.boot.style : null);
              }).catch(function (e) { toast(e.message, 'error'); });
          }
        }
      ],
      after: function () {
        $('#dlgDefs').value = sampleDefs;
        $('#dlgCode').value = sample;
        $('#dlgName').value = '';
        $('#dlgPyFile').addEventListener('change', function (e) {
          var f = e.target.files[0];
          if (!f) return;
          f.text().then(function (txt) {
            $('#dlgCode').value = txt;
            if (!$('#dlgName').value) $('#dlgName').value = f.name.replace(/\.py$/i, '');
          });
        });
      }
    });
  }

  /* ---------------- boot style options ---------------- */

  function renderBootStyleOptions(selected) {
    var sel = $('#bootStyle');
    if (!sel) return;
    sel.innerHTML = '';
    S.effects.forEach(function (fx) {
      var op = document.createElement('option');
      op.value = 'builtin:' + fx.id;
      op.textContent = effectLabel(fx);
      sel.appendChild(op);
    });
    if (S.styles.length) {
      var group = document.createElement('optgroup');
      group.label = t('styles.mine');
      S.styles.forEach(function (st) {
        var op = document.createElement('option');
        op.value = st.id;
        op.textContent = st.name;
        group.appendChild(op);
      });
      sel.appendChild(group);
    }
    if (selected) {
      var found = Array.prototype.some.call(sel.options, function (o) { return o.value === selected; });
      if (found) sel.value = selected;
    }
  }

  /* ---------------- picker ---------------- */

  function setPickerColor(hex) {
    var rgb = hexToRgb(hex);
    var hsv = rgbToHsv(rgb[0], rgb[1], rgb[2]);
    S.picker.h = hsv[0];
    S.picker.s = hsv[1];
    S.picker.v = hsv[2];
    updatePickerUI();
  }

  function updatePickerUI() {
    var hex = pickerHex();
    var rgb = hexToRgb(hex);
    $('#svArea').style.background = 'hsl(' + S.picker.h.toFixed(0) + ', 100%, 50%)';
    $('#svCursor').style.left = (S.picker.s * 100) + '%';
    $('#svCursor').style.top = ((1 - S.picker.v) * 100) + '%';
    $('#hueCursor').style.left = (S.picker.h / 360 * 100) + '%';
    $('#pickPreview').style.background = hex;
    if (document.activeElement !== $('#pickHex')) $('#pickHex').value = hex;
    $('#pickR').value = rgb[0]; $('#pickG').value = rgb[1]; $('#pickB').value = rgb[2];
    $('#pickRv').textContent = rgb[0]; $('#pickGv').textContent = rgb[1]; $('#pickBv').textContent = rgb[2];
  }

  function openPicker(target, initial) {
    S.pickerTarget = target;
    setPickerColor(initial || S.color);
    openModal('#colorModal');
  }

  function bindPicker() {
    function svFromEvent(e) {
      var r = $('#svArea').getBoundingClientRect();
      S.picker.s = clamp((e.clientX - r.left) / r.width, 0, 1);
      S.picker.v = 1 - clamp((e.clientY - r.top) / r.height, 0, 1);
      updatePickerUI();
    }
    function hueFromEvent(e) {
      var r = $('#hueSlider').getBoundingClientRect();
      S.picker.h = clamp((e.clientX - r.left) / r.width, 0, 1) * 360;
      updatePickerUI();
    }
    function drag(node, handler) {
      var active = false;
      node.addEventListener('pointerdown', function (e) {
        active = true;
        try { node.setPointerCapture(e.pointerId); } catch (err) { }
        handler(e);
        e.preventDefault();
      });
      node.addEventListener('pointermove', function (e) {
        if (active) handler(e);
      });
      node.addEventListener('pointerup', function () { active = false; });
      node.addEventListener('pointercancel', function () { active = false; });
    }
    drag($('#svArea'), svFromEvent);
    drag($('#hueSlider'), hueFromEvent);

    $('#pickHex').addEventListener('input', function () {
      var v = $('#pickHex').value.trim();
      var m = /^#?([0-9a-fA-F]{6})$/.exec(v);
      if (m) setPickerColor('#' + m[1].toUpperCase());
    });
    ['R', 'G', 'B'].forEach(function (ch) {
      $('#pick' + ch).addEventListener('input', function () {
        var r = +$('#pickR').value, g = +$('#pickG').value, b = +$('#pickB').value;
        var hsv = rgbToHsv(r, g, b);
        S.picker.h = hsv[0]; S.picker.s = hsv[1]; S.picker.v = hsv[2];
        updatePickerUI();
      });
    });

    $('#pickOk').addEventListener('click', function () {
      var hex = pickerHex();
      var tgt = S.pickerTarget;
      closeModal('#colorModal');
      if (!tgt) return;
      if (tgt.kind === 'solid') {
        setCurrentColor(hex);
        markLocal();
        S.selectedId = 'builtin:solid';
        S.params = { color: hex };
        renderSelection();
        applyNow();
      } else if (tgt.kind === 'param') {
        S.params[tgt.key] = hex;
        markLocal();
        renderParamPanel();
        scheduleApply();
      } else if (tgt.kind === 'paramColor') {
        var arr = S.params[tgt.key];
        if (Array.isArray(arr) && arr[tgt.index] !== undefined) arr[tgt.index] = hex;
        markLocal();
        renderParamPanel();
        scheduleApply();
      }
    });
  }

  /* ---------------- dialogs ---------------- */

  function openModal(sel) {
    var m = $(sel);
    m.classList.add('open');
    m.setAttribute('aria-hidden', 'false');
  }

  function closeModal(sel) {
    var m = $(sel);
    m.classList.remove('open');
    m.setAttribute('aria-hidden', 'true');
  }

  function openDialog(opts) {
    $('#dlgTitle').textContent = opts.title;
    $('#dlgBody').innerHTML = opts.body || '';
    var actions = $('#dlgActions');
    actions.innerHTML = '';
    var close = function () { closeModal('#dialogModal'); };
    (opts.actions || []).forEach(function (a) {
      var b = el('button', a.cls || 'ghost-btn', a.label);
      b.addEventListener('click', function () { a.onClick ? a.onClick(close) : close(); });
      actions.appendChild(b);
    });
    openModal('#dialogModal');
    if (opts.after) opts.after();
  }

  function showLogs() {
    api('/api/log').then(function (d) {
      var text = (d.logs || []).join('\n') || '(empty)';
      openDialog({
        title: t('dlg.logsTitle'),
        body: '<pre class="code">' + esc(text) + '</pre>',
        actions: [{ label: t('common.close'), cls: 'primary-btn', onClick: function (close) { close(); } }]
      });
    }).catch(function (e) { toast(e.message, 'error'); });
  }

  function confirmReboot() {
    openDialog({
      title: t('dlg.rebootTitle'),
      body: '<p>' + esc(t('dlg.rebootBody')) + '</p>',
      actions: [
        { label: t('common.cancel'), onClick: function (close) { close(); } },
        {
          label: t('settings.reboot'), cls: 'danger-btn', onClick: function (close) {
            close();
            api('/api/reboot', 'POST', {}).then(function () {
              toast(t('toast.reboot'));
              setOnline(false);
            }).catch(function () { toast(t('toast.reboot')); });
          }
        }
      ]
    });
  }

  /* ---------------- settings ---------------- */

  function fillSettings(cfg) {
    if (!cfg) return;
    $('#setLeds').value = cfg.hardware.leds;
    $('#setPins').value = (cfg.hardware.pins || []).join(', ');
    $('#setFps').value = cfg.render.fps;
    $('#fpsVal').textContent = cfg.render.fps;
    $('#setOrder').value = cfg.render.color_order || 'RGB';
    $('#bootMode').value = cfg.boot.mode === 'off' ? 'off' : 'preset';
    $('#bootBright').value = cfg.boot.brightness;
    $('#bootBrightVal').textContent = cfg.boot.brightness;
    $('#setSsid').value = cfg.wifi.ssid;
    $('#setPass').value = cfg.wifi.password;
    renderBootStyleOptions(cfg.boot.style);
    S.settingsFilled = true;
  }

  function saveHardware() {
    var leds = parseInt($('#setLeds').value, 10);
    var fps = parseInt($('#setFps').value, 10);
    var pins = $('#setPins').value.split(',').map(function (x) { return parseInt(x.trim(), 10); })
      .filter(function (n) { return !isNaN(n) && n >= 0 && n <= 48; });
    if (!pins.length) pins = [2];
    if (!leds || leds < 1) { toast(t('toast.invalidValue'), 'error'); return; }
    if (!fps || fps < 5) fps = 30;
    api('/api/settings', 'PUT', {
      hardware: { leds: leds, pins: pins },
      render: { fps: fps, color_order: $('#setOrder').value }
    }).then(function (d) {
      S.settings = d.settings;
      fillSettings(d.settings);
      toast(d.reboot_required ? t('toast.rebootRequired') : t('toast.saved'));
      return refreshState(true);
    }).catch(function (e) { toast(e.message, 'error'); });
  }

  function saveBootSettings() {
    var mode = $('#bootMode').value;
    api('/api/settings', 'PUT', {
      boot: {
        mode: mode,
        style: $('#bootStyle').value,
        params: {},
        brightness: parseInt($('#bootBright').value, 10),
        power: mode !== 'off'
      }
    }).then(function (d) {
      S.settings = d.settings;
      fillSettings(d.settings);
      toast(t('toast.saved'));
    }).catch(function (e) { toast(e.message, 'error'); });
  }

  function saveWifi() {
    var ssid = $('#setSsid').value.trim();
    if (!ssid) { toast(t('toast.invalidValue'), 'error'); return; }
    api('/api/settings', 'PUT', {
      wifi: { ssid: ssid, password: $('#setPass').value }
    }).then(function (d) {
      S.settings = d.settings;
      fillSettings(d.settings);
      toast(d.reboot_required ? t('toast.rebootRequired') : t('toast.saved'));
    }).catch(function (e) { toast(e.message, 'error'); });
  }

  function useCurrentBoot() {
    if (!S.selectedId) { toast(t('toast.noSelection'), 'error'); return; }
    api('/api/save-boot', 'POST', {
      style_id: S.selectedId, params: S.params,
      brightness: parseInt($('#bootBright').value, 10),
      power: true
    }).then(function () {
      toast(t('toast.saved'));
      return refreshState(true);
    }).then(function () {
      if (S.settings) fillSettings(S.settings);
    }).catch(function (e) { toast(e.message, 'error'); });
  }

  /* ---------------- state sync ---------------- */

  function applyState(d) {
    S.device = d.device || {};
    S.settings = d.settings || null;
    S.runtime = d.runtime || {};
    if (!S.settingsFilled && S.settings) fillSettings(S.settings);
    renderRuntime();
    syncSelection();
  }

  function syncSelection() {
    var rt = S.runtime || {};
    if (!rt.style_id) return;
    if (Date.now() - S.lastLocal < 4000) return;
    if (rt.style_id === S.selectedId) return;
    S.selectedId = rt.style_id;
    S.params = rt.style_params ? JSON.parse(JSON.stringify(rt.style_params)) : {};
    renderSelection();
  }

  function refreshState(silent) {
    return api('/api/state').then(function (d) {
      applyState(d);
      setOnline(true);
    }).catch(function (e) {
      if (window.console && console.warn) {
        console.warn('state failed:', (e && e.stack) ? e.stack : e);
      }
      setOnline(false);
    });
  }

  function loadEffects() {
    return api('/api/effects').then(function (d) {
      S.effects = d.effects || [];
    });
  }

  function loadStyles() {
    return api('/api/styles').then(function (d) {
      S.styles = d.styles || [];
      return S.styles;
    });
  }

  function loadColors() {
    return api('/api/colors').then(function (d) {
      S.colors = d.colors || [];
    });
  }

  function saveColor() {
    var list = S.colors.slice();
    if (list.indexOf(S.color) < 0) list.push(S.color);
    api('/api/colors', 'PUT', { colors: list }).then(function (d) {
      S.colors = d.colors || list;
      renderColorSwatches();
      toast(t('toast.colorSaved'));
    }).catch(function (e) { toast(e.message, 'error'); });
  }

  /* ---------------- events ---------------- */

  function switchPage(name) {
    $$('.page').forEach(function (p) {
      p.classList.toggle('active', p.id === 'page-' + name);
    });
    $$('.tab').forEach(function (b) {
      b.classList.toggle('active', b.getAttribute('data-page') === name);
    });
    if (name !== 'styles') $('#paramPanel').classList.remove('open');
    if (name === 'settings' && S.settings) fillSettings(S.settings);
    if (name === 'styles') renderSelection();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function bindEvents() {
    $$('.tab').forEach(function (b) {
      b.addEventListener('click', function () { switchPage(b.getAttribute('data-page')); });
    });
    $$('[data-goto]').forEach(function (b) {
      b.addEventListener('click', function () { switchPage(b.getAttribute('data-goto')); });
    });

    $('#langBtn').addEventListener('click', function () {
      setLang(S.lang === 'zh' ? 'en' : 'zh');
    });
    $('#themeBtn').addEventListener('click', function () {
      applyTheme(S.theme === 'dark' ? 'light' : 'dark');
    });

    $('#powerBtn').addEventListener('click', function () {
      var on = !(S.runtime && S.runtime.power);
      api('/api/power', 'POST', { on: on }).then(function (d) {
        S.runtime.power = d.power;
        renderRuntime();
      }).catch(function (e) { toast(e.message, 'error'); });
    });

    var brightnessPost = debounce(function (v) {
      api('/api/brightness', 'POST', { value: v }).then(function (d) {
        S.runtime.brightness = d.brightness;
      }).catch(function (e) { toast(e.message, 'error'); });
    }, 220);
    $('#brightness').addEventListener('input', function () {
      var v = parseInt($('#brightness').value, 10);
      $('#brightVal').textContent = v;
      brightnessPost(v);
    });
    $('#brightPresets').addEventListener('click', function (e) {
      var btn = e.target.closest('[data-value]');
      if (!btn) return;
      var v = parseInt(btn.getAttribute('data-value'), 10);
      $('#brightness').value = v;
      $('#brightVal').textContent = v;
      markLocal();
      api('/api/brightness', 'POST', { value: v }).then(function (d) {
        S.runtime.brightness = d.brightness;
      }).catch(function (err) { toast(err.message, 'error'); });
    });

    $('#currentColor').addEventListener('click', function () {
      openPicker({ kind: 'solid' }, S.color);
    });
    $('#saveColorBtn').addEventListener('click', saveColor);

    $('#saveStyleBtn').addEventListener('click', saveCurrentStyle);
    $('#savePresetBtn').addEventListener('click', saveCurrentStyle);
    $('#importBtn').addEventListener('click', function () { $('#importFile').click(); });
    $('#importFile').addEventListener('change', function (e) {
      var f = e.target.files[0];
      if (f) importStyleFile(f);
      e.target.value = '';
    });
    $('#newPyBtn').addEventListener('click', newPythonStyle);

    $('#closeParamBtn').addEventListener('click', function () {
      $('#paramPanel').classList.remove('open');
    });

    $('#applyBootBtn').addEventListener('click', function () {
      if (!S.selectedId) { toast(t('toast.noSelection'), 'error'); return; }
      api('/api/save-boot', 'POST', {
        style_id: S.selectedId, params: S.params,
        brightness: S.runtime.brightness !== undefined ? S.runtime.brightness : 128,
        power: true
      }).then(function () {
        toast(t('toast.saved'));
        return refreshState(true);
      }).catch(function (e) { toast(e.message, 'error'); });
    });

    $('#setFps').addEventListener('input', function () {
      $('#fpsVal').textContent = $('#setFps').value;
    });
    $('#bootBright').addEventListener('input', function () {
      $('#bootBrightVal').textContent = $('#bootBright').value;
    });
    $('#saveHwBtn').addEventListener('click', saveHardware);
    $('#saveBootBtn').addEventListener('click', saveBootSettings);
    $('#saveWifiBtn').addEventListener('click', saveWifi);
    $('#useCurrentBootBtn').addEventListener('click', useCurrentBoot);
    $('#logBtn').addEventListener('click', showLogs);
    $('#rebootBtn').addEventListener('click', confirmReboot);

    $$('.modal').forEach(function (m) {
      m.addEventListener('click', function (e) {
        if (e.target === m) m.classList.remove('open');
      });
      $$('[data-close]', m).forEach(function (b) {
        b.addEventListener('click', function () { m.classList.remove('open'); });
      });
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        $$('.modal.open').forEach(function (m) { m.classList.remove('open'); });
      }
    });

    document.addEventListener('visibilitychange', function () {
      if (!document.hidden) refreshState(true);
    });
  }

  /* ---------------- boot ---------------- */

  function startPolling() {
    if (S.pollTimer) clearInterval(S.pollTimer);
    S.pollTimer = setInterval(function () {
      if (!document.hidden) refreshState(true);
    }, 3000);
  }

  function init() {
    var savedLang = localStorage.getItem('ws.lang');
    S.lang = savedLang || ((navigator.language || 'zh').toLowerCase().indexOf('zh') === 0 ? 'zh' : 'en');
    var savedTheme = localStorage.getItem('ws.theme');
    S.theme = savedTheme === 'dark' ? 'dark' : 'light';
    S.color = localStorage.getItem('ws.color') || '#FF6600';

    applyTheme(S.theme);
    applyI18n();
    setCurrentColor(S.color);
    bindEvents();
    bindPicker();

    refreshState(false)
      .then(loadEffects)
      .then(loadStyles)
      .then(loadColors)
      .then(function () {
        renderEffects();
        renderQuickEffects();
        renderStyles();
        renderColorSwatches();
        if (S.settings) {
          renderBootStyleOptions(S.settings.boot.style);
        }
        syncSelection();
        renderSelection();
      })
      .catch(function (e) {
        if (window.console && console.warn) console.warn('init failed:', e);
        toast(e.message, 'error');
      });

    startPolling();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

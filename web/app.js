(() => {
  "use strict";

  const $ = selector => document.querySelector(selector);
  const $$ = selector => [...document.querySelectorAll(selector)];
  const refs = {
    songList: $("#songList"), songCount: $("#songCount"), songFilter: $("#songFilter"),
    bibleSelect: $("#bibleSelect"), bookSelect: $("#bookSelect"), chapterSelect: $("#chapterSelect"),
    verseSelect: $("#verseSelect"), verseToSelect: $("#verseToSelect"), bibleJoin: $("#bibleJoin"),
    bibleQuick: $("#bibleQuick"), bibleQuickGo: $("#bibleQuickGo"), bibleQuickHint: $("#bibleQuickHint"),
    biblePrevChapter: $("#biblePrevChapter"), bibleNextChapter: $("#bibleNextChapter"),
    mediaGrid: $("#mediaGrid"), mediaCount: $("#mediaCount"), mediaDrop: $("#mediaDrop"), uploadBar: $("#uploadBar"),
    slidesGrid: $("#slidesGrid"), slidesTitle: $("#slidesTitle"), slideCounter: $("#slideCounter"),
    currentTitle: $("#currentTitle"), previewFrame: $("#previewFrame"), previewBg: $("#previewBg"),
    previewOverlay: $("#previewOverlay"), previewLabel: $("#previewLabel"), previewText: $("#previewText"),
    previewReference: $("#previewReference"), previewCopy: $("#previewCopy"), videoHint: $("#videoHint"),
    stagePreviewFrame: $("#stagePreviewFrame"), stagePreviewBg: $("#stagePreviewBg"),
    stagePreviewOverlay: $("#stagePreviewOverlay"), stagePreviewLabel: $("#stagePreviewLabel"),
    stagePreviewText: $("#stagePreviewText"), stagePreviewReference: $("#stagePreviewReference"),
    stagePreviewCopy: $("#stagePreviewCopy"), stageVideoHint: $("#stageVideoHint"),
    stagePreviewBlackout: $("#stagePreviewBlackout"), monitorStatus: $("#monitorStatus"), monitorHelp: $("#monitorHelp"),
    onAir: $("#onAir"), goLive: $("#goLive"), blackout: $("#blackout"),
    backgroundName: $("#backgroundName"), backgroundSwatch: $("#backgroundSwatch"), overlayName: $("#overlayName"),
    fontSize: $("#fontSize"), fontSizeNumber: $("#fontSizeNumber"), fontFamily: $("#fontFamily"),
    fontWeight: $("#fontWeight"), styleTarget: $("#styleTarget"), inspectorContext: $("#inspectorContext"),
    textColor: $("#textColor"), textColorValue: $("#textColorValue"), textShadow: $("#textShadow"), uppercase: $("#uppercase"),
    italic: $("#italic"), textOutline: $("#textOutline"), textBackground: $("#textBackground"),
    positionX: $("#positionX"), positionXOut: $("#positionXOut"), positionY: $("#positionY"), positionYOut: $("#positionYOut"),
    maxWidth: $("#maxWidth"), maxWidthOut: $("#maxWidthOut"), lineHeight: $("#lineHeight"), lineHeightOut: $("#lineHeightOut"),
    letterSpacing: $("#letterSpacing"), letterSpacingOut: $("#letterSpacingOut"),
    txtInput: $("#txtInput"), bibleInput: $("#bibleInput"), mediaInput: $("#mediaInput"), fontInput: $("#fontInput"), settingsInput: $("#settingsInput"),
    onlineDialog: $("#onlineDialog"), onlineQuery: $("#onlineQuery"), onlineResults: $("#onlineResults"),
    obsUrl: $("#obsUrl"), clockPreview: $("#clockPreview"), clockDate: $("#clockDate"), clockLabel: $("#clockLabel"),
    clock24: $("#clock24"), clockSeconds: $("#clockSeconds"), clockShowDate: $("#clockShowDate"), clockDateFormat: $("#clockDateFormat"),
    bibleShowVersion: $("#bibleShowVersion"), bibleReferenceFormat: $("#bibleReferenceFormat"),
    ljaDialog: $("#ljaDialog"), ljaQuery: $("#ljaQuery"), ljaResults: $("#ljaResults"), ljaQuickStatus: $("#ljaQuickStatus"), ljaDialogStatus: $("#ljaDialogStatus"), ljaBibleQuickStatus: $("#ljaBibleQuickStatus"),
    ljaStatusDot: $("#ljaStatusDot"), ljaStatusTitle: $("#ljaStatusTitle"), ljaStatusDetail: $("#ljaStatusDetail"), ljaPath: $("#ljaPath"),
    screenSelect: $("#screenSelect"), screenHelp: $("#screenHelp"), screenFill: $("#screenFill"),
    uiAccent: $("#uiAccent"), uiScale: $("#uiScale"), uiScaleOut: $("#uiScaleOut"), uiDensity: $("#uiDensity"),
    confirmDelete: $("#confirmDelete"), confirmClear: $("#confirmClear"), crossfadeMs: $("#crossfadeMs"), crossfadeOut: $("#crossfadeOut"), previewMode: $("#previewMode"),
    songShowLabels: $("#songShowLabels"), songShowCredits: $("#songShowCredits"), songCreditsFormat: $("#songCreditsFormat"),
    ytInput: $("#ytInput"), ytAdd: $("#ytAdd"), ytTools: $("#ytTools"), ytRemote: $("#ytRemote"), ytNowTitle: $("#ytNowTitle"), ytNowInfo: $("#ytNowInfo"), ytSeek: $("#ytSeek"), ytTime: $("#ytTime"), ytDur: $("#ytDur"), ytBack: $("#ytBack"), ytPlay: $("#ytPlay"), ytFwd: $("#ytFwd"), ytVolume: $("#ytVolume"), ytVolText: $("#ytVolText"), ytMute: $("#ytMute"), ytQuality: $("#ytQuality"), ytStop: $("#ytStop"), ytCount: $("#ytCount"), ytList: $("#ytList"), ytDefaultHeight: $("#ytDefaultHeight"), ytAutoDownload: $("#ytAutoDownload"), ytAutoSwitch: $("#ytAutoSwitch"), ytUpdateTools: $("#ytUpdateTools"),
    fontCount: $("#fontCount"), fontAutoImport: $("#fontAutoImport"), fontSyncNow: $("#fontSyncNow"), fontSyncStatus: $("#fontSyncStatus"), slideDialog: $("#slideDialog"), slideDialogTitle: $("#slideDialogTitle"), slideLabel: $("#slideLabel"), slideText: $("#slideText"),
    songEditTitle: $("#songEditTitle"), songEditArtist: $("#songEditArtist"), songEditAlbum: $("#songEditAlbum"),
    aboutVersion: $("#aboutVersion"), aboutSystem: $("#aboutSystem"), aboutController: $("#aboutController"),
    aboutObs: $("#aboutObs"), aboutDataPath: $("#aboutDataPath"), aboutGithub: $("#aboutGithub"),
    updatePill: $("#updatePill"), updatePillText: $("#updatePillText"), updateStatus: $("#updateStatus"), checkUpdates: $("#checkUpdates"), installUpdate: $("#installUpdate"), openDataFolder: $("#openDataFolder")
  };

  const app = {
    songs: [], bibles: [], ljaBibles: [], media: [], fonts: [], settings: {}, defaults: {},
    state: null, deck: [], deckTitle: "", selectedSongId: "", currentIndex: -1,
    pickerMode: "background", monitorView: "output", draftMode: "song", visualEditorMode: "", styleTarget: "song.text",
    videoFrameCache: new Map(), toastTimer: null, settingsTimer: null, visualTimer: null,
    bibleBooks: [], bibleChapter: null, bibleRestored: false,
    ljaStatus: null, ljaBibleStatus: null, screens: [], screenDetails: null, screenEventsBound: false, editingSlide: -1, drag: null,
    appInfo: null, updateInfo: null
  };

  const STYLE_TARGETS = {
    song: [
      ["song.text", "Letra da música"],
      ["song.label", "Rótulo da seção"],
      ["song.reference", "Créditos / referência"]
    ],
    bible: [
      ["bible.text", "Texto bíblico"],
      ["bible.reference", "Livro, capítulo e verso"],
      ["bible.version", "Versão da Bíblia"]
    ],
    clock: [
      ["clock.time", "Hora"],
      ["clock.label", "Texto auxiliar"],
      ["clock.date", "Data"]
    ]
  };

  async function api(path, options = {}) {
    const response = await fetch(path, {
      ...options,
      headers: { "Content-Type": "application/json", ...(options.headers || {}) }
    });
    let payload = null;
    try { payload = await response.json(); } catch (_) { payload = {}; }
    if (!response.ok) throw new Error(payload.error || `Erro ${response.status}`);
    return payload;
  }

  function toast(title, message = "") {
    clearTimeout(app.toastTimer);
    $("#toastTitle").textContent = title;
    $("#toastMessage").textContent = message;
    $("#toast").classList.add("show");
    app.toastTimer = setTimeout(() => $("#toast").classList.remove("show"), 3300);
  }

  function formatBytes(bytes) {
    if (!bytes) return "0 KB";
    const units = ["B", "KB", "MB", "GB"];
    const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), 3);
    return `${(bytes / 1024 ** index).toFixed(index > 1 ? 1 : 0)} ${units[index]}`;
  }

  function setUpdateStatus(message, state = "idle") {
    refs.updateStatus.textContent = message;
    refs.updateStatus.dataset.state = state;
  }

  async function loadAbout() {
    try {
      const info = await api("/api/about");
      app.appInfo = info;
      refs.aboutVersion.textContent = info.version;
      refs.aboutSystem.textContent = info.system;
      refs.aboutController.textContent = info.controllerUrl;
      refs.aboutObs.textContent = info.obsUrl;
      refs.aboutDataPath.textContent = info.dataPath;
      refs.aboutGithub.href = info.repository;
      refs.aboutGithub.textContent = info.repository.replace(/^https?:\/\//, "");
      if (!info.installedBuild) {
        setUpdateStatus("Modo Python: a atualização automática é usada somente na versão instalada do Windows.");
      }
    } catch (error) {
      setUpdateStatus(`Não foi possível carregar as informações: ${error.message}`, "error");
    }
  }

  // Quando há versão nova o NexStage inteiro fica laranja e aparece um aviso no topo.
  function setUpdateBadge(available, version) {
    document.body.classList.toggle("update-ready", available);
    refs.updatePill.hidden = !available;
    if (available) refs.updatePillText.textContent = version ? `Atualização disponível • ${version}` : "Atualização disponível";
  }

  async function checkForUpdates(silent = false, force = false) {
    refs.checkUpdates.disabled = true;
    if (!silent) setUpdateStatus("Consultando a release mais recente no GitHub…");
    try {
      const info = await api(`/api/update/check${force ? "?force=1" : ""}`);
      app.updateInfo = info;
      refs.installUpdate.hidden = !(info.available && info.downloadReady && info.updateSupported);
      setUpdateBadge(Boolean(info.available), info.latestVersion);
      if (info.available) {
        const size = info.downloadSize ? ` • ${formatBytes(info.downloadSize)}` : "";
        const suffix = info.updateSupported
          ? `${size} Clique em “Baixar e instalar”.`
          : " Abra a página de releases para baixar manualmente.";
        setUpdateStatus(`${info.message}${suffix}`, "available");
        if (!silent) toast(`NexStage ${info.latestVersion} disponível`, "A atualização é opcional.");
      } else {
        setUpdateStatus(info.message, "ok");
        if (!silent) toast("NexStage atualizado", info.message);
      }
    } catch (error) {
      refs.installUpdate.hidden = true;
      setUpdateStatus(error.message, "error");
      if (!silent) toast("Falha ao verificar atualização", error.message);
    } finally {
      refs.checkUpdates.disabled = false;
    }
  }

  async function installAvailableUpdate() {
    const version = app.updateInfo?.latestVersion || "mais recente";
    if (!confirm(`Baixar e instalar o NexStage ${version}?\n\nO NexStage será encerrado e o instalador será aberto.`)) return;
    refs.installUpdate.disabled = true;
    refs.checkUpdates.disabled = true;
    setUpdateStatus("Baixando o instalador oficial… mantenha o NexStage aberto.", "available");
    try {
      const result = await api("/api/update/apply", { method: "POST", body: "{}" });
      setUpdateStatus(result.message, "ok");
      toast("Atualização pronta", "O instalador será aberto em instantes.");
    } catch (error) {
      refs.installUpdate.disabled = false;
      refs.checkUpdates.disabled = false;
      setUpdateStatus(error.message, "error");
      toast("Não foi possível atualizar", error.message);
    }
  }

  function isVideo(url) { return /\.(mp4|webm|mov|m4v)(?:\?|$)/i.test(url || ""); }

  function switchTab(name) {
    if (name === "youtube") ytStartPolling(); else ytStopPolling();
    $$(".rail-button").forEach(button => button.classList.toggle("active", button.dataset.tab === name));
    $$(".tab-panel").forEach(panel => panel.classList.toggle("active", panel.dataset.panel === name));
    if (name === "clock") {
      app.draftMode = "clock";
      setMonitorView("draft");
      renderPreview();
    } else if (name === "songs") {
      app.visualEditorMode = "";
      app.draftMode = "song";
      if (app.deck.length) renderPreview();
    } else if (name === "bible") {
      app.visualEditorMode = "";
      app.draftMode = "bible";
      if (app.deck.length) renderPreview();
      restoreBibleOnce();
    } else if ((name === "songs" || name === "bible") && app.deck.length) {
      renderPreview();
    }
    if (name === "songs" || name === "bible" || name === "clock") syncStyleEditor();
  }

  function makeIcon(id) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
    use.setAttribute("href", `#${id}`);
    svg.append(use);
    return svg;
  }

  function renderSongs() {
    const filter = refs.songFilter.value.trim().toLocaleLowerCase("pt-BR");
    const songs = app.songs.filter(song => `${song.title} ${song.artist || ""}`.toLocaleLowerCase("pt-BR").includes(filter));
    refs.songCount.textContent = app.songs.length;
    refs.songList.replaceChildren();
    if (!songs.length) {
      const empty = document.createElement("div");
      empty.className = "dialog-empty";
      empty.textContent = app.songs.length ? "Nenhum resultado." : "Importe sua primeira música em TXT.";
      refs.songList.append(empty);
      return;
    }
    songs.forEach(song => {
      const item = document.createElement("div");
      item.className = `library-item${song.id === app.selectedSongId ? " active" : ""}`;
      const icon = document.createElement("span"); icon.className = "library-icon"; icon.append(makeIcon("i-music"));
      const meta = document.createElement("span"); meta.className = "library-meta";
      const title = document.createElement("b"); title.textContent = song.title;
      const detail = document.createElement("small"); detail.textContent = `${song.slides.length} slides • ${song.artist || song.source || "TXT"}`;
      meta.append(title, detail);
      const remove = document.createElement("button"); remove.className = "item-delete"; remove.title = "Excluir"; remove.append(makeIcon("i-trash"));
      remove.addEventListener("click", async event => {
        event.stopPropagation();
        if (app.settings.ui?.confirmDelete !== false && !confirm(`Excluir “${song.title}” da biblioteca?`)) return;
        try {
          await api(`/api/song/${encodeURIComponent(song.id)}`, { method: "DELETE" });
          app.songs = app.songs.filter(candidate => candidate.id !== song.id);
          if (app.selectedSongId === song.id) clearDeck();
          renderSongs(); toast("Música excluída");
        } catch (error) { toast("Não foi possível excluir", error.message); }
      });
      item.append(icon, meta, remove);
      item.addEventListener("click", () => selectSong(song));
      refs.songList.append(item);
    });
  }

  function selectSong(song) {
    app.visualEditorMode = "";
    app.selectedSongId = song.id;
    app.deckTitle = song.title;
    const credit = songCredit(song);
    app.deck = song.slides.map(slide => ({
      text: slide.text,
      sectionLabel: slide.label || "",
      label: app.settings.song?.showSectionLabels === false ? "" : (slide.label || ""),
      reference: credit
    }));
    app.currentIndex = app.deck.length ? 0 : -1;
    app.draftMode = "song";
    if (!app.state.live) app.monitorView = "draft";
    refs.currentTitle.textContent = song.title;
    refs.slidesTitle.textContent = song.title;
    renderSongs(); renderSlides(); syncStyleEditor(); renderPreview();
  }

  function clearDeck() {
    app.selectedSongId = ""; app.deck = []; app.deckTitle = ""; app.currentIndex = -1;
    refs.currentTitle.textContent = "Selecione uma música";
    refs.slidesTitle.textContent = "Nenhum item selecionado";
    app.draftMode = "song";
    renderSlides(); renderPreview();
  }

  function renderSlides() {
    refs.slideCounter.textContent = `${app.deck.length} slide${app.deck.length === 1 ? "" : "s"}`;
    refs.slidesGrid.replaceChildren();
    if (!app.deck.length) {
      const empty = document.createElement("div"); empty.className = "empty-state";
      empty.append(makeIcon("i-music"));
      const bold = document.createElement("b"); bold.textContent = "Sua sequência aparecerá aqui";
      const text = document.createElement("span"); text.textContent = "Importe um TXT ou selecione uma passagem bíblica.";
      empty.append(bold, text); refs.slidesGrid.append(empty); return;
    }
    app.deck.forEach((slide, index) => {
      const card = document.createElement("div");
      card.className = `slide-card${index === app.currentIndex ? " active" : ""}`;
      const number = document.createElement("span"); number.className = "slide-number"; number.textContent = String(index + 1).padStart(2, "0");
      const label = document.createElement("small"); label.textContent = slide.sectionLabel || slide.label || slide.reference || "SLIDE";
      const text = document.createElement("p"); text.textContent = slide.text;
      card.append(number, label, text);
      if (app.selectedSongId) {
        const edit = document.createElement("button"); edit.className = "slide-edit"; edit.title = "Editar slide"; edit.append(makeIcon("i-edit"));
        edit.addEventListener("click", event => { event.stopPropagation(); openSlideEditor(index); });
        card.append(edit);
      }
      card.addEventListener("click", () => presentSlide(index, true));
      if (app.selectedSongId) card.addEventListener("dblclick", event => { event.preventDefault(); openSlideEditor(index); });
      refs.slidesGrid.append(card);
    });
  }

  const PREVIEW_GRADIENT = "radial-gradient(circle at 18% 25%, #1766a3 0, transparent 32%), radial-gradient(circle at 90% 90%, #113e70 0, transparent 36%), linear-gradient(145deg, #0e2036, #070a10 65%)";

  function selectedSlide() {
    return app.deck[app.currentIndex] || null;
  }

  function songCredit(song) {
    if (!song || app.settings.song?.showCredits !== true) return "";
    const artist = String(song.artist || "").trim();
    const album = String(song.album || "").trim();
    if (app.settings.song?.creditsFormat === "titleArtist") return [song.title, artist].filter(Boolean).join(" — ");
    if (app.settings.song?.creditsFormat === "album") return album;
    return artist;
  }

  function refreshSongDeckOptions() {
    const song = app.songs.find(item => item.id === app.selectedSongId); if (!song) return;
    const credit = songCredit(song);
    app.deck.forEach((slide, index) => {
      const original = slide.sectionLabel ?? song.slides[index]?.label ?? slide.label ?? "";
      slide.sectionLabel = original;
      slide.label = app.settings.song?.showSectionLabels === false ? "" : original;
      slide.reference = credit;
    });
    renderSlides(); renderPreview(); saveSettings();
    if (app.state.live && app.state.mode === "song" && app.draftMode !== "bible" && app.draftMode !== "clock") pushState(buildLyricsState(true));
  }

  function clockDraft() {
    return {
      format24: refs.clock24.checked,
      showSeconds: refs.clockSeconds.checked,
      showDate: refs.clockShowDate.checked,
      dateFormat: refs.clockDateFormat.value,
      label: refs.clockLabel.value.trim()
    };
  }

  function formatClockContent(clock = {}) {
    const now = new Date();
    let reference = "";
    if (clock.showDate !== false && clock.dateFormat === "short") {
      reference = new Intl.DateTimeFormat("pt-BR").format(now);
    } else if (clock.showDate !== false && clock.dateFormat === "weekday") {
      reference = new Intl.DateTimeFormat("pt-BR", { weekday: "long" }).format(now);
    } else if (clock.showDate !== false) {
      reference = new Intl.DateTimeFormat("pt-BR", {
        weekday: "long", day: "2-digit", month: "long"
      }).format(now);
    }
    return {
      text: new Intl.DateTimeFormat("pt-BR", {
        hour: "2-digit", minute: "2-digit",
        second: clock.showSeconds ? "2-digit" : undefined,
        hour12: clock.format24 === false
      }).format(now),
      label: clock.label || "",
      reference
    };
  }

  function captureVideoFrame(url) {
    if (app.videoFrameCache.has(url)) return app.videoFrameCache.get(url);
    const task = new Promise(resolve => {
      const video = document.createElement("video");
      let settled = false;
      let timer = null;

      const finish = frame => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        video.pause();
        video.removeAttribute("src");
        try { video.load(); } catch (_) {}
        resolve(frame);
      };

      const draw = () => {
        if (settled || video.readyState < 2 || !video.videoWidth || !video.videoHeight) return;
        try {
          const canvas = document.createElement("canvas");
          canvas.width = 640; canvas.height = 360;
          const scale = Math.max(canvas.width / video.videoWidth, canvas.height / video.videoHeight);
          const sourceWidth = canvas.width / scale;
          const sourceHeight = canvas.height / scale;
          const sourceX = (video.videoWidth - sourceWidth) / 2;
          const sourceY = (video.videoHeight - sourceHeight) / 2;
          canvas.getContext("2d").drawImage(video, sourceX, sourceY, sourceWidth, sourceHeight, 0, 0, canvas.width, canvas.height);
          finish(canvas.toDataURL("image/jpeg", 0.76));
        } catch (_) { finish(""); }
      };

      video.muted = true;
      video.playsInline = true;
      video.preload = "metadata";
      video.disablePictureInPicture = true;
      video.addEventListener("loadedmetadata", () => {
        const duration = Number(video.duration);
        if (Number.isFinite(duration) && duration > 0.12) {
          const target = Math.min(Math.max(duration * 0.05, 0.12), 0.75, Math.max(0, duration - 0.02));
          try { video.currentTime = target; } catch (_) { draw(); }
        } else {
          draw();
        }
      }, { once: true });
      video.addEventListener("seeked", draw, { once: true });
      video.addEventListener("loadeddata", draw, { once: true });
      video.addEventListener("error", () => finish(""), { once: true });
      timer = setTimeout(() => { draw(); if (!settled) finish(""); }, 6000);
      video.src = url;
      video.load();
    });
    if (app.videoFrameCache.size >= 8) app.videoFrameCache.delete(app.videoFrameCache.keys().next().value);
    app.videoFrameCache.set(url, task);
    return task;
  }

  function setPreviewBackground(element, hint, url) {
    url = url || "";
    if (element.dataset.source === url) return;
    element.dataset.source = url;
    element.style.backgroundImage = PREVIEW_GRADIENT;
    hint.style.display = "none";
    if (!url) return;
    if (!isVideo(url)) {
      element.style.backgroundImage = `linear-gradient(#05080d33,#05080d33), url("${url.replaceAll('"', '%22')}")`;
      return;
    }
    hint.style.display = "flex";
    if (app.settings.performance?.previewMode === "off") {
      hint.querySelector("span").textContent = "vídeo selecionado";
      return;
    }
    hint.querySelector("span").textContent = "carregando frame";
    captureVideoFrame(url).then(frame => {
      if (element.dataset.source !== url) return;
      if (frame) {
        element.style.backgroundImage = `linear-gradient(#05080d33,#05080d33), url("${frame}")`;
        hint.querySelector("span").textContent = hint === refs.stageVideoHint ? "frame" : "quadro congelado do vídeo";
      } else {
        hint.querySelector("span").textContent = "vídeo selecionado";
      }
    });
  }

  function setPreviewOverlay(element, url, theme, hidden = false) {
    if (!url || hidden) {
      element.style.display = "none";
      return;
    }
    if (element.getAttribute("src") !== url) element.src = url;
    element.style.opacity = String(theme.overlayOpacity ?? 1);
    element.style.display = "block";
  }

  function hexRgba(hex, opacity) {
    const value = String(hex || "#000000").replace("#", "");
    const full = value.length === 3 ? value.split("").map(part => part + part).join("") : value;
    const number = Number.parseInt(full, 16);
    if (!Number.isFinite(number)) return `rgba(0,0,0,${opacity})`;
    return `rgba(${number >> 16},${(number >> 8) & 255},${number & 255},${opacity})`;
  }

  function visualStyles(state) {
    const styles = state.styles || app.state?.styles || {};
    if (state.mode === "clock") return { label: styles.clock?.label || {}, text: styles.clock?.time || {}, reference: styles.clock?.date || {} };
    if (state.mode === "bible") return { label: styles.bible?.version || {}, text: styles.bible?.text || {}, reference: styles.bible?.reference || {} };
    return { label: styles.song?.label || {}, text: styles.song?.text || {}, reference: styles.song?.reference || {} };
  }

  function applyPreviewBlock(element, style, frameHeight, compact) {
    const scale = frameHeight / 1080;
    element.style.left = `${Number(style.x ?? 50)}%`;
    element.style.top = `${Number(style.y ?? 50)}%`;
    element.style.width = `${Number(style.maxWidth ?? 86)}%`;
    element.style.fontFamily = style.fontFamily || "Arial, Helvetica, sans-serif";
    element.style.fontSize = `${Math.max(compact ? 3.2 : 6.5, Number(style.fontSize || 64) * scale)}px`;
    element.style.fontWeight = String(style.fontWeight || 400);
    element.style.color = style.textColor || "#ffffff";
    element.style.textAlign = style.align || "center";
    element.style.lineHeight = String(style.lineHeight || 1.13);
    element.style.letterSpacing = `${Number(style.letterSpacing || 0) * scale}px`;
    element.style.textTransform = style.uppercase ? "uppercase" : "none";
    element.style.fontStyle = style.italic ? "italic" : "normal";
    element.style.textShadow = style.shadow === false ? "none" : `0 ${Math.max(1, 3 * scale)}px ${Math.max(2, 12 * scale)}px #000, 0 1px 2px #000`;
    element.style.webkitTextStroke = style.outline ? `${Math.max(.25, 1.5 * scale)}px #000` : "0 transparent";
    element.style.background = style.background ? hexRgba(style.backgroundColor, Number(style.backgroundOpacity ?? .35)) : "transparent";
    element.style.padding = style.background ? `${Math.max(1, 8 * scale)}px ${Math.max(2, 14 * scale)}px` : "0";
    element.style.borderRadius = style.background ? `${Math.max(1, 8 * scale)}px` : "0";
  }

  function applyPreviewTheme(target, state, compact = false) {
    const frameHeight = target.frame.getBoundingClientRect().height || (compact ? 105 : 280);
    const styles = visualStyles(state);
    applyPreviewBlock(target.label, styles.label, frameHeight, compact);
    applyPreviewBlock(target.text, styles.text, frameHeight, compact);
    applyPreviewBlock(target.reference, styles.reference, frameHeight, compact);
    if (!compact) {
      target.label.classList.add("drag-target"); target.label.dataset.kind = "label";
      target.text.classList.add("drag-target"); target.text.dataset.kind = "text";
      target.reference.classList.add("drag-target"); target.reference.dataset.kind = "reference";
    }
  }

  function renderVisual(target, state, placeholder, compact = false, black = false) {
    const content = state.mode === "youtube"
      ? { label: "YOUTUBE", text: state.youtube?.title || "Vídeo do YouTube", reference: "" }
      : state.mode === "clock" ? formatClockContent(state.clock) : (state.slide || {});
    target.label.textContent = content.label || "";
    target.text.textContent = content.text || placeholder;
    target.reference.textContent = content.reference || "";
    applyPreviewTheme(target, state, compact);
    setPreviewBackground(target.background, target.videoHint, state.background);
    setPreviewOverlay(target.overlay, state.overlay, state.theme || {}, black);
  }

  function buildDraftPreviewState() {
    const slide = selectedSlide() || { text: "", label: "", reference: "" };
    if (app.draftMode === "clock") {
      return { ...app.state, live: false, black: false, mode: "clock", clock: clockDraft(), slide: { text: "", label: "", reference: "" } };
    }
    return {
      ...app.state, live: false, black: false,
      mode: app.draftMode === "bible" ? "bible" : "song",
      slide: { text: slide.text || "", label: slide.label || "", reference: slide.reference || "" }
    };
  }

  function renderLyricsPreview() {
    if (app.visualEditorMode === "clock") {
      renderVisual({
        frame: refs.previewFrame, background: refs.previewBg, overlay: refs.previewOverlay,
        copy: refs.previewCopy, label: refs.previewLabel, text: refs.previewText,
        reference: refs.previewReference, videoHint: refs.videoHint
      }, buildDraftPreviewState(), "Relógio");
      return;
    }
    const fallback = app.state?.mode !== "clock" ? app.state?.slide : null;
    const slide = selectedSlide() || fallback || { text: "", label: "", reference: "" };
    const state = {
      ...app.state, black: false, mode: app.draftMode === "bible" ? "bible" : "song",
      slide: { text: slide.text || "", label: slide.label || "", reference: slide.reference || "" }
    };
    renderVisual({
      frame: refs.previewFrame, background: refs.previewBg, overlay: refs.previewOverlay,
      copy: refs.previewCopy, label: refs.previewLabel, text: refs.previewText,
      reference: refs.previewReference, videoHint: refs.videoHint
    }, state, "Escolha uma música ou um verso");
  }

  function renderMonitorPreview() {
    if (!app.state) return;
    const isDraft = app.monitorView === "draft";
    const state = isDraft ? buildDraftPreviewState() : app.state;
    const black = !isDraft && Boolean(state.black);
    renderVisual({
      frame: refs.stagePreviewFrame, background: refs.stagePreviewBg, overlay: refs.stagePreviewOverlay,
      copy: refs.stagePreviewCopy, label: refs.stagePreviewLabel, text: refs.stagePreviewText,
      reference: refs.stagePreviewReference, videoHint: refs.stageVideoHint
    }, state, "Nada selecionado", true, black);
    refs.stagePreviewBlackout.classList.toggle("visible", black);
    refs.monitorStatus.className = "monitor-status";
    if (isDraft) {
      refs.monitorStatus.textContent = "PRÉVIA";
      refs.monitorHelp.textContent = "Mostra o relógio ou visual preparado sem enviá-lo ao público.";
    } else if (black) {
      refs.monitorStatus.textContent = "PRETO";
      refs.monitorStatus.classList.add("black");
      refs.monitorHelp.textContent = "O telão do público está totalmente preto.";
    } else if (state.live) {
      refs.monitorStatus.textContent = "NO AR";
      refs.monitorStatus.classList.add("live");
      refs.monitorHelp.textContent = "Espelho do conteúdo que está no monitor do público.";
    } else {
      refs.monitorStatus.textContent = "FORA DO AR";
      refs.monitorStatus.classList.add("off");
      refs.monitorHelp.textContent = "A saída está limpa; o último visual permanece disponível para conferência.";
    }
    $$("[data-monitor-view]").forEach(button => button.classList.toggle("active", button.dataset.monitorView === app.monitorView));
  }

  function setMonitorView(view) {
    app.monitorView = view === "draft" ? "draft" : "output";
    renderMonitorPreview();
  }

  function renderPreview() {
    if (!app.state) return;
    renderLyricsPreview();
    renderMonitorPreview();
    updateMediaLabels();
  }

  function buildLyricsState(live = app.state.live) {
    const slide = selectedSlide() || { text: "", label: "", reference: "" };
    return {
      ...app.state, live, black: false,
      mode: app.draftMode === "bible" ? "bible" : "song",
      slide: { text: slide.text || "", label: slide.label || "", reference: slide.reference || "" },
      styles: app.state.styles, fonts: app.fonts,
      videoCrossfadeMs: app.settings.videoCrossfadeMs ?? 450
    };
  }

  function buildClockState(live = app.state.live) {
    return {
      ...app.state, live, black: false, mode: "clock", clock: clockDraft(), styles: app.state.styles, fonts: app.fonts,
      slide: { text: "", label: "", reference: "" },
      videoCrossfadeMs: app.settings.videoCrossfadeMs ?? 450
    };
  }

  function buildVisualState(live = app.state.live) {
    return { ...app.state, live, styles: app.state.styles, fonts: app.fonts, videoCrossfadeMs: app.settings.videoCrossfadeMs ?? 450 };
  }

  async function pushState(next) {
    app.state = next;
    updateLiveUi(); renderPreview();
    try {
      app.state = await api("/api/state", { method: "POST", body: JSON.stringify(next) });
      updateLiveUi(); renderPreview();
    } catch (error) { toast("Saída desconectada", error.message); }
  }

  function presentSlide(index, forceLive) {
    if (!app.deck[index]) return;
    app.currentIndex = index;
    if (app.draftMode !== "bible") app.draftMode = "song";
    app.monitorView = "output";
    renderSlides(); renderPreview();
    pushState(buildLyricsState(forceLive ? true : app.state.live));
  }

  function updateLiveUi() {
    const live = Boolean(app.state?.live && !app.state?.black);
    refs.onAir.classList.toggle("live", live);
    refs.onAir.querySelector("b").textContent = live ? "NO AR" : "FORA DO AR";
    refs.goLive.classList.toggle("live", live);
    refs.goLive.querySelector("b").textContent = live ? "ATUALIZAR AO VIVO" : "COLOCAR NO AR";
    refs.blackout.classList.toggle("active", Boolean(app.state?.black));
  }

  function renderBibles() {
    const selected = refs.bibleSelect.value;
    const total = app.bibles.length + app.ljaBibles.length;
    refs.bibleSelect.replaceChildren(new Option(total ? "Selecione a tradução" : "Importe XML ou conecte o Louvor JA", ""));
    if (app.ljaBibles.length) {
      const group = document.createElement("optgroup"); group.label = "Louvor JA • offline";
      app.ljaBibles.forEach(bible => group.append(new Option(`${bible.abbreviation} — ${bible.name}`, `lja:${bible.id}`)));
      refs.bibleSelect.append(group);
    }
    if (app.bibles.length) {
      const group = document.createElement("optgroup"); group.label = "Bíblias XML importadas";
      app.bibles.forEach(bible => group.append(new Option(`${bible.name} (${bible.bookCount} livros)`, bible.id)));
      refs.bibleSelect.append(group);
    }
    if ([...refs.bibleSelect.options].some(option => option.value === selected)) refs.bibleSelect.value = selected;
  }

  function selectedBibleSource() {
    const value = refs.bibleSelect.value;
    if (value.startsWith("lja:")) return { type: "lja", id: Number(value.slice(4)) };
    return { type: "xml", id: value };
  }

  // Guarda onde o usuário está (livro, capítulo, versículo) para continuar no mesmo ponto ao trocar de tradução.
  function captureBibleContext() {
    const chapter = app.bibleChapter;
    if (!chapter || !refs.bookSelect.value) return null;
    const pos = app.bibleBooks.findIndex(book => String(book.index) === refs.bookSelect.value);
    return {
      name: chapter.book, abbr: chapter.bookAbbreviation || "", pos, count: app.bibleBooks.length,
      chapter: Number(chapter.chapter), verse: Number(refs.verseSelect.value) || 0, to: Number(refs.verseToSelect.value) || 0
    };
  }

  function findBookByContext(context) {
    const key = NexBibleRef.bookKey;
    let pos = app.bibleBooks.findIndex(book => key(book.name) === key(context.name));
    if (pos < 0 && context.abbr) pos = app.bibleBooks.findIndex(book => book.abbreviation && key(book.abbreviation) === key(context.abbr));
    if (pos < 0 && context.pos >= 0 && context.count === app.bibleBooks.length) pos = context.pos;
    return pos;
  }

  function resetVerseControls() {
    app.bibleChapter = null;
    refs.verseSelect.replaceChildren(new Option("Todos", "")); refs.verseSelect.disabled = true;
    refs.verseToSelect.replaceChildren(new Option("—", "")); refs.verseToSelect.disabled = true;
    refs.bibleJoin.disabled = true;
  }

  async function bibleChanged({ context = null, push = true } = {}) {
    const previous = context || captureBibleContext();
    refs.bookSelect.disabled = true; refs.chapterSelect.disabled = true;
    refs.chapterSelect.replaceChildren(new Option("—", ""));
    if (!refs.bibleSelect.value) {
      refs.bookSelect.replaceChildren(new Option("—", "")); app.bibleBooks = []; resetVerseControls();
      return;
    }
    refs.bookSelect.replaceChildren(new Option("Carregando…", ""));
    try {
      const source = selectedBibleSource();
      const books = source.type === "lja"
        ? await api(`/api/louvorja/bible/books?version=${encodeURIComponent(source.id)}`)
        : await api(`/api/bible/${encodeURIComponent(source.id)}/books`);
      app.bibleBooks = books;
      refs.bookSelect.replaceChildren(new Option("Selecione o livro", ""));
      books.forEach(book => {
        const option = new Option(book.name, String(book.index));
        option.dataset.chapters = book.chapterCount;
        option.dataset.abbreviation = book.abbreviation || "";
        refs.bookSelect.add(option);
      });
      refs.bookSelect.disabled = false;
      if (!previous) { resetVerseControls(); return; }
      // Troca de tradução: continua no mesmo livro, capítulo e versículo.
      const pos = findBookByContext(previous);
      if (pos < 0) { resetVerseControls(); return; }
      const fits = previous.chapter >= 1 && previous.chapter <= books[pos].chapterCount;
      await openBibleAt(pos, fits ? previous.chapter : 1, { verse: fits ? previous.verse : 0, to: fits ? previous.to : 0, push });
    } catch (error) { toast("Erro ao abrir a Bíblia", error.message); }
  }

  function bookChanged() {
    refs.chapterSelect.replaceChildren(new Option("Selecione", ""));
    const option = refs.bookSelect.selectedOptions[0];
    const count = Number(option?.dataset.chapters || 0);
    const source = selectedBibleSource();
    for (let index = 0; index < count; index++) {
      const value = source.type === "lja" ? index + 1 : index;
      refs.chapterSelect.add(new Option(String(index + 1), String(value)));
    }
    refs.chapterSelect.disabled = !count;
  }

  function bibleReference(book, chapter, verse, abbreviation = "", verseEnd = 0) {
    const span = verseEnd && Number(verseEnd) > Number(verse) ? `${verse}-${verseEnd}` : `${verse}`;
    if (refs.bibleReferenceFormat.value === "compact") {
      const shortBook = abbreviation || String(book).split(/\s+/)[0].slice(0, 2);
      return `${shortBook} ${chapter}.${span}`;
    }
    return `${book} ${chapter}:${span}`;
  }

  function verseNumbers() {
    return (app.bibleChapter?.verses || []).map(verse => Number(verse.number)).filter(Number.isFinite);
  }

  // Preenche "Versículo" e "Até" com os versículos do capítulo aberto.
  function fillVerseSelects(verse = 0, to = 0) {
    const numbers = verseNumbers();
    refs.verseSelect.replaceChildren(new Option("Todos", ""));
    numbers.forEach(number => refs.verseSelect.add(new Option(String(number), String(number))));
    refs.verseSelect.disabled = !numbers.length;
    refs.verseSelect.value = numbers.includes(verse) ? String(verse) : "";
    refreshVerseTo(to);
  }

  function refreshVerseTo(wanted = null) {
    const from = Number(refs.verseSelect.value) || 0;
    const keep = wanted === null ? refs.verseToSelect.value : (wanted ? String(wanted) : "");
    refs.verseToSelect.replaceChildren(new Option("—", ""));
    if (from) verseNumbers().filter(number => number > from).forEach(number => refs.verseToSelect.add(new Option(String(number), String(number))));
    refs.verseToSelect.disabled = !from || refs.verseToSelect.options.length < 2;
    if ([...refs.verseToSelect.options].some(option => option.value === keep)) refs.verseToSelect.value = keep;
    refs.bibleJoin.disabled = !(from && Number(refs.verseToSelect.value));
  }

  function bibleIsRange() {
    const from = Number(refs.verseSelect.value) || 0;
    const to = Number(refs.verseToSelect.value) || 0;
    return Boolean(from && to > from);
  }

  // Monta os slides: capítulo inteiro (começando no versículo escolhido) ou só o intervalo.
  function buildBibleDeck() {
    const chapter = app.bibleChapter;
    if (!chapter) return;
    const from = Number(refs.verseSelect.value) || 0;
    const to = Number(refs.verseToSelect.value) || 0;
    const make = (text, verse, verseEnd = 0) => ({
      text,
      label: refs.bibleShowVersion.checked ? chapter.bible : "",
      reference: bibleReference(chapter.book, chapter.chapter, verse, chapter.bookAbbreviation, verseEnd),
      bible: { version: chapter.bible, versionName: chapter.bibleName || chapter.bible, book: chapter.book, bookAbbreviation: chapter.bookAbbreviation || "", chapter: chapter.chapter, verse, verseEnd }
    });
    const inRange = bibleIsRange() ? chapter.verses.filter(verse => Number(verse.number) >= from && Number(verse.number) <= to) : [];
    if (inRange.length) {
      app.deck = refs.bibleJoin.checked && !refs.bibleJoin.disabled
        ? [make(inRange.map(verse => `${verse.number} ${verse.text}`).join(" "), from, to)]
        : inRange.map(verse => make(verse.text, verse.number));
      app.currentIndex = 0;
      app.deckTitle = `${chapter.book} ${chapter.chapter}:${from}-${to}`;
    } else {
      app.deck = chapter.verses.map(verse => make(verse.text, verse.number));
      const index = from ? chapter.verses.findIndex(verse => Number(verse.number) === from) : 0;
      app.currentIndex = app.deck.length ? Math.max(0, index) : -1;
      app.deckTitle = `${chapter.book} ${chapter.chapter}`;
    }
    refs.currentTitle.textContent = app.deckTitle; refs.slidesTitle.textContent = app.deckTitle;
  }

  function bibleIsOnAir() {
    return Boolean(app.state.live && !app.state.black && app.state.mode === "bible");
  }

  // Guarda a última passagem (e a opção de juntar) para reabrir o programa no mesmo ponto.
  function rememberBible() {
    const chapter = app.bibleChapter;
    if (!chapter || !refs.bibleSelect.value) return;
    const pos = app.bibleBooks.findIndex(book => String(book.index) === refs.bookSelect.value);
    app.settings.bible = {
      ...(app.settings.bible || {}),
      last: {
        source: refs.bibleSelect.value, name: chapter.book, abbr: chapter.bookAbbreviation || "", pos, count: app.bibleBooks.length,
        chapter: Number(chapter.chapter), verse: Number(refs.verseSelect.value) || 0, to: Number(refs.verseToSelect.value) || 0
      }
    };
    saveSettings();
  }

  // Carrega o capítulo escolhido nas caixas. push: se já houver uma Bíblia no ar, atualiza o telão.
  async function openChapter({ verse = 0, to = 0, push = false, present = false, last = false } = {}) {
    if (refs.chapterSelect.value === "" || refs.bookSelect.value === "") return false;
    try {
      const source = selectedBibleSource();
      const chapter = source.type === "lja"
        ? await api(`/api/louvorja/bible/chapter?version=${encodeURIComponent(source.id)}&book=${encodeURIComponent(refs.bookSelect.value)}&chapter=${encodeURIComponent(refs.chapterSelect.value)}`)
        : await api(`/api/bible/${encodeURIComponent(source.id)}/chapter?book=${refs.bookSelect.value}&chapter=${refs.chapterSelect.value}`);
      app.selectedSongId = "";
      app.bibleChapter = chapter;
      fillVerseSelects(Number(verse) || 0, Number(to) || 0);
      buildBibleDeck();
      if (last && app.deck.length) app.currentIndex = app.deck.length - 1;
      app.visualEditorMode = "";
      app.draftMode = "bible";
      if (!app.state.live) app.monitorView = "draft";
      renderSongs(); renderSlides(); syncStyleEditor(); renderPreview();
      if (app.deck.length && (present || (push && bibleIsOnAir()))) presentSlide(app.currentIndex, true);
      rememberBible();
      return true;
    } catch (error) { toast("Erro ao abrir capítulo", error.message); return false; }
  }

  // Abre livro (posição na lista) e capítulo (1, 2, 3…) por código.
  async function openBibleAt(pos, chapterNumber, options = {}) {
    const book = app.bibleBooks[pos];
    if (!book) return false;
    refs.bookSelect.value = String(book.index); bookChanged();
    refs.chapterSelect.value = String(selectedBibleSource().type === "lja" ? chapterNumber : chapterNumber - 1);
    return openChapter(options);
  }

  function chapterChanged() { return openChapter(); }

  function verseChanged() {
    refreshVerseTo();
    applyBibleSelection();
  }

  // Versículo, "até" ou "juntar" mudou: remonta os slides sem recarregar o capítulo.
  function applyBibleSelection() {
    if (!app.bibleChapter) return;
    refs.bibleJoin.disabled = !bibleIsRange();
    buildBibleDeck();
    app.selectedSongId = ""; app.draftMode = "bible";
    if (!app.state.live) app.monitorView = "draft";
    renderSlides(); renderPreview();
    if (app.deck.length && bibleIsOnAir()) presentSlide(app.currentIndex, true);
    rememberBible();
  }

  // direction: +1 próximo capítulo, -1 anterior (passa para o livro vizinho nas pontas).
  async function stepBibleChapter(direction, options = {}) {
    const chapter = app.bibleChapter;
    let pos = app.bibleBooks.findIndex(book => String(book.index) === refs.bookSelect.value);
    if (!chapter || pos < 0) return false;
    let number = Number(chapter.chapter) + direction;
    if (number < 1) { pos -= 1; if (pos < 0) return false; number = app.bibleBooks[pos].chapterCount; }
    else if (number > app.bibleBooks[pos].chapterCount) { pos += 1; if (pos >= app.bibleBooks.length) return false; number = 1; }
    return openBibleAt(pos, number, { push: true, ...options });
  }

  // Setas e botões: troca de versículo; no fim do capítulo, segue para o próximo (e volta ao anterior no começo).
  async function stepSlide(direction) {
    if (app.draftMode === "bible" && app.bibleChapter && !bibleIsRange()) {
      const next = app.currentIndex + direction;
      if (next >= app.deck.length && await stepBibleChapter(1, { present: true })) return;
      if (next < 0 && await stepBibleChapter(-1, { present: true, last: true })) return;
    }
    presentSlide(Math.max(0, Math.min(app.deck.length - 1, app.currentIndex + direction)), true);
  }

  function setQuickHint(text, kind = "") {
    refs.bibleQuickHint.textContent = text;
    refs.bibleQuickHint.className = `bible-quick-hint${kind ? ` ${kind}` : ""}`;
  }

  function describeReference(ref) {
    const book = app.bibleBooks[ref.pos];
    const span = ref.verse ? `:${ref.verse}${ref.to ? `-${ref.to}` : ""}` : "";
    return `${book.name} ${ref.chapter}${span}`;
  }

  function bibleQuickPreview() {
    const text = refs.bibleQuick.value.trim();
    if (!text) return setQuickHint("Digite e aperte Enter. Depois use ← → para trocar de versículo.");
    if (!app.bibleBooks.length) return setQuickHint("Escolha a tradução (ou aperte Enter para usar a última).");
    const ref = NexBibleRef.resolve(text, app.bibleBooks);
    if (!ref) return setQuickHint("Livro não reconhecido…", "error");
    const book = app.bibleBooks[ref.pos];
    if (ref.chapter > book.chapterCount) return setQuickHint(`${book.name} tem só ${book.chapterCount} capítulos.`, "error");
    setQuickHint(`→ ${describeReference(ref)}`, "ok");
  }

  async function bibleQuickGo() {
    const text = refs.bibleQuick.value.trim();
    if (!text) return;
    if (!refs.bibleSelect.value) {
      const last = app.settings.bible?.last?.source;
      const options = [...refs.bibleSelect.options].filter(option => option.value);
      const choice = options.find(option => option.value === last) || options[0];
      if (!choice) return setQuickHint("Nenhuma Bíblia disponível. Importe um XML ou conecte o Louvor JA.", "error");
      refs.bibleSelect.value = choice.value;
      await bibleChanged();
    }
    const ref = NexBibleRef.resolve(text, app.bibleBooks);
    if (!ref) return setQuickHint(`Não entendi “${text}”. Exemplos: jo 3:16 · sl 23 · 1co 13:4-7`, "error");
    const book = app.bibleBooks[ref.pos];
    if (ref.chapter > book.chapterCount) return setQuickHint(`${book.name} tem só ${book.chapterCount} capítulos.`, "error");
    app.bibleRestored = true; // a referência digitada vale mais que a última passagem guardada
    switchTab("bible");
    const opened = await openBibleAt(ref.pos, ref.chapter, { verse: ref.verse, to: ref.to, push: true });
    if (!opened) return;
    let note = describeReference(ref);
    if (ref.verse && Number(refs.verseSelect.value) !== ref.verse) note = `${book.name} ${ref.chapter} (versículo ${ref.verse} não existe nesta tradução)`;
    else if (ref.to && Number(refs.verseToSelect.value) !== ref.to) note = `${book.name} ${ref.chapter}:${ref.verse} (o intervalo passa do fim do capítulo)`;
    setQuickHint(`Aberto: ${note}`, "ok");
    refs.bibleQuick.select();
    refs.bibleQuick.blur(); // devolve o teclado às setas ← →
  }

  // Reabre a última passagem usada, sem mexer no telão. Só roda quando a aba Bíblia está aberta,
  // para não trocar os slides que estão na tela enquanto a pessoa trabalha com músicas.
  async function restoreBibleOnce() {
    if (app.bibleRestored || refs.bibleSelect.value) return;
    if ($(".tab-panel.active")?.dataset.panel !== "bible") return;
    const last = app.settings.bible?.last;
    if (!last?.source || ![...refs.bibleSelect.options].some(option => option.value === last.source)) return;
    app.bibleRestored = true;
    refs.bibleSelect.value = last.source;
    await bibleChanged({ context: last, push: false });
  }

  function bibleSettingsChanged() {
    app.settings.bible = { ...(app.settings.bible || {}), showVersion: refs.bibleShowVersion.checked, referenceFormat: refs.bibleReferenceFormat.value };
    if (app.draftMode === "bible") {
      app.deck.forEach(slide => {
        if (!slide.bible) return;
        slide.label = refs.bibleShowVersion.checked ? slide.bible.version : "";
        slide.reference = bibleReference(slide.bible.book, slide.bible.chapter, slide.bible.verse, slide.bible.bookAbbreviation, slide.bible.verseEnd);
      });
      renderSlides(); renderPreview();
      if (app.state.live && app.state.mode === "bible") pushState(buildLyricsState(true));
    }
    saveSettings();
  }

  function renderMedia() {
    refs.mediaCount.textContent = app.media.length;
    refs.mediaGrid.replaceChildren();
    if (!app.media.length) {
      const empty = document.createElement("div"); empty.className = "dialog-empty"; empty.textContent = "Nenhuma mídia importada."; empty.style.gridColumn = "1/-1"; refs.mediaGrid.append(empty); return;
    }
    app.media.forEach(media => {
      const card = document.createElement("div"); card.className = `media-card${app.state.background === media.url || app.state.overlay === media.url ? " active" : ""}`;
      if (media.type === "image") {
        const image = document.createElement("img"); image.src = media.url; image.alt = media.name; image.loading = "lazy"; card.append(image);
      } else {
        const thumb = document.createElement("div"); thumb.className = "media-video-thumb"; thumb.append(makeIcon("i-play")); card.append(thumb);
      }
      const label = document.createElement("span"); label.textContent = media.name; label.title = `${media.name} • ${formatBytes(media.size)}`; card.append(label);
      card.addEventListener("click", () => chooseMedia(media)); refs.mediaGrid.append(card);
    });
  }

  function chooseMedia(media) {
    if (app.pickerMode === "overlay") {
      if (media.type !== "image") { toast("Escolha uma imagem", "A sobreposição deve ser PNG, JPG, WebP ou GIF."); return; }
      app.state.overlay = media.url;
    } else {
      app.state.background = media.url;
    }
    renderMedia(); renderPreview(); saveSettings();
    if (app.state.live) pushState(buildVisualState(true));
    toast(app.pickerMode === "overlay" ? "Logo selecionada" : "Fundo selecionado", media.name);
  }

  function updateMediaLabels() {
    const background = app.media.find(item => item.url === app.state.background);
    refs.backgroundName.textContent = background?.name || "Gradiente padrão";
    if (background?.type === "image") refs.backgroundSwatch.style.backgroundImage = `url("${background.url}")`;
    else refs.backgroundSwatch.style.backgroundImage = "radial-gradient(circle at 25% 20%, #2276b6, transparent 46%), linear-gradient(145deg,#172c43,#0c131d)";
    const overlay = app.media.find(item => item.url === app.state.overlay);
    refs.overlayName.textContent = overlay?.name || "Nenhuma logo";
  }

  function uploadMedia(file) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest(); xhr.open("POST", "/api/media/upload");
      xhr.setRequestHeader("X-Filename", encodeURIComponent(file.name));
      xhr.upload.onprogress = event => { if (event.lengthComputable) refs.uploadBar.style.width = `${event.loaded / event.total * 100}%`; };
      xhr.onerror = () => reject(new Error("Falha de rede durante o envio"));
      xhr.onload = () => {
        let payload = {}; try { payload = JSON.parse(xhr.responseText); } catch (_) {}
        if (xhr.status >= 200 && xhr.status < 300) resolve(payload); else reject(new Error(payload.error || `Erro ${xhr.status}`));
      };
      xhr.send(file);
    });
  }

  async function handleMediaFiles(files) {
    const accepted = [...files]; if (!accepted.length) return;
    for (let index = 0; index < accepted.length; index++) {
      const file = accepted[index];
      try {
        refs.uploadBar.style.width = "0";
        const item = await uploadMedia(file); app.media.unshift(item);
        toast("Mídia importada", `${file.name} (${index + 1}/${accepted.length})`);
      } catch (error) { toast(`Falha em ${file.name}`, error.message); }
    }
    refs.uploadBar.style.width = "0"; renderMedia();
  }

  async function readTextSmart(file) {
    const buffer = await file.arrayBuffer();
    let text = new TextDecoder("utf-8").decode(buffer);
    const bad = (text.match(/�/g) || []).length;
    if (bad > 2) text = new TextDecoder("windows-1252").decode(buffer);
    return text;
  }

  async function importTxtFiles(files) {
    for (const file of files) {
      try {
        const song = await api("/api/song/import", { method: "POST", body: JSON.stringify({ filename: file.name, content: await readTextSmart(file) }) });
        app.songs.push(song); toast("Música importada", song.title);
      } catch (error) { toast(`Falha em ${file.name}`, error.message); }
    }
    renderSongs();
  }

  async function importBibleFile(file) {
    if (!file) return;
    try {
      const bible = await api("/api/bible/import", { method: "POST", body: JSON.stringify({ filename: file.name, content: await readTextSmart(file) }) });
      app.bibles.push(bible); renderBibles(); refs.bibleSelect.value = bible.id; await bibleChanged();
      toast("Bíblia importada", `${bible.name} • ${bible.bookCount} livros`);
    } catch (error) { toast("Não foi possível importar o XML", error.message); }
  }

  async function searchOnline() {
    const query = refs.onlineQuery.value.trim(); if (!query) return;
    refs.onlineResults.replaceChildren();
    const loading = document.createElement("div"); loading.className = "dialog-empty"; loading.textContent = "Buscando letras…"; refs.onlineResults.append(loading);
    try {
      const results = await api(`/api/lyrics/search?q=${encodeURIComponent(query)}`);
      refs.onlineResults.replaceChildren();
      if (!results.length) { loading.textContent = "Nenhuma letra encontrada. Tente incluir o artista."; refs.onlineResults.append(loading); return; }
      results.forEach(result => {
        const row = document.createElement("div"); row.className = "online-result";
        const meta = document.createElement("div"); const title = document.createElement("b"); title.textContent = result.title;
        const detail = document.createElement("small"); detail.textContent = [result.artist, result.album].filter(Boolean).join(" • "); meta.append(title, detail);
        const button = document.createElement("button"); button.textContent = "IMPORTAR";
        button.type = "button";
        button.addEventListener("click", async () => {
          button.disabled = true; button.textContent = "…";
          try {
            const song = await api("/api/lyrics/import", { method: "POST", body: JSON.stringify({ title: result.title, artist: result.artist, filename: `${result.title}.txt`, lyrics: result.lyrics }) });
            app.songs.push(song); renderSongs(); selectSong(song); refs.onlineDialog.close(); toast("Letra importada", `${result.title} — confira antes de apresentar`);
          } catch (error) { toast("Falha ao importar", error.message); button.disabled = false; button.textContent = "IMPORTAR"; }
        });
        row.append(meta, button); refs.onlineResults.append(row);
      });
    } catch (error) { refs.onlineResults.replaceChildren(loading); loading.textContent = error.message; }
  }

  function clone(value) { return JSON.parse(JSON.stringify(value)); }

  function renderFontFaces() {
    let style = document.getElementById("nexstage-fonts");
    if (!style) { style = document.createElement("style"); style.id = "nexstage-fonts"; document.head.append(style); }
    style.textContent = app.fonts.map(font =>
      `@font-face{font-family:"${String(font.family).replaceAll('"', '')}";src:url("${String(font.url).replaceAll('"', '%22')}") format("${font.format || 'truetype'}");font-display:swap;}`
    ).join("\n");
  }

  function populateFontOptions() {
    const selected = refs.fontFamily.value;
    refs.fontFamily.querySelectorAll("optgroup").forEach(group => group.remove());
    if (app.fonts.length) {
      const group = document.createElement("optgroup"); group.label = "Fontes importadas";
      app.fonts.forEach(font => group.append(new Option(font.name, `"${font.family}"`)));
      refs.fontFamily.append(group);
    }
    if ([...refs.fontFamily.options].some(option => option.value === selected)) refs.fontFamily.value = selected;
    refs.fontCount.textContent = `${app.fonts.length} fonte${app.fonts.length === 1 ? "" : "s"} importada${app.fonts.length === 1 ? "" : "s"}`;
  }

  function styleMode() {
    return app.draftMode === "bible" ? "bible" : app.draftMode === "clock" ? "clock" : "song";
  }

  function styleAt(path = app.styleTarget) {
    const [section, component] = String(path).split(".");
    return app.state.styles?.[section]?.[component] || null;
  }

  function syncStyleEditor(preferred = "") {
    const mode = styleMode();
    const targets = STYLE_TARGETS[mode];
    refs.styleTarget.replaceChildren(...targets.map(([value, label]) => new Option(label, value)));
    const candidate = preferred || (String(app.styleTarget).startsWith(`${mode}.`) ? app.styleTarget : targets[0][0]);
    app.styleTarget = targets.some(([value]) => value === candidate) ? candidate : targets[0][0];
    refs.styleTarget.value = app.styleTarget;
    refs.inspectorContext.textContent = mode === "bible" ? "Bíblia" : mode === "clock" ? "Relógio" : "Música";
    applyStyleControls();
  }

  function applyStyleControls() {
    const style = styleAt(); if (!style) return;
    const fontSize = validFontSize(style.fontSize, 64);
    refs.fontSize.value = Math.max(Number(refs.fontSize.min), Math.min(Number(refs.fontSize.max), fontSize));
    refs.fontSizeNumber.value = String(fontSize);
    refs.fontFamily.value = style.fontFamily || "Arial, Helvetica, sans-serif";
    if (!refs.fontFamily.value && style.fontFamily) refs.fontFamily.add(new Option(style.fontFamily, style.fontFamily, true, true));
    refs.fontWeight.value = String(style.fontWeight || 400);
    refs.textColor.value = style.textColor || "#ffffff"; refs.textColorValue.textContent = refs.textColor.value.toUpperCase();
    refs.textShadow.checked = style.shadow !== false; refs.uppercase.checked = Boolean(style.uppercase);
    refs.italic.checked = Boolean(style.italic); refs.textOutline.checked = Boolean(style.outline); refs.textBackground.checked = Boolean(style.background);
    refs.positionX.value = style.x ?? 50; refs.positionXOut.value = `${style.x ?? 50}%`;
    refs.positionY.value = style.y ?? 50; refs.positionYOut.value = `${style.y ?? 50}%`;
    refs.maxWidth.value = style.maxWidth ?? 86; refs.maxWidthOut.value = `${style.maxWidth ?? 86}%`;
    refs.lineHeight.value = style.lineHeight ?? 1.13; refs.lineHeightOut.value = Number(style.lineHeight ?? 1.13).toFixed(2);
    refs.letterSpacing.value = style.letterSpacing ?? 0; refs.letterSpacingOut.value = `${style.letterSpacing ?? 0} px`;
    $$('[data-align]').forEach(button => button.classList.toggle("active", button.dataset.align === (style.align || "center")));
  }

  function validFontSize(value, fallback = 64) {
    const number = Number(value);
    return Number.isFinite(number) && number > 0 ? number : fallback;
  }

  function fontSizeChanged(source) {
    const style = styleAt(); if (!style) return;
    const value = validFontSize(source === "number" ? refs.fontSizeNumber.value : refs.fontSize.value, style.fontSize || 64);
    style.fontSize = value;
    if (source === "range") refs.fontSizeNumber.value = String(value);
    else refs.fontSize.value = Math.max(Number(refs.fontSize.min), Math.min(Number(refs.fontSize.max), value));
    renderPreview(); saveSettings(); scheduleVisualPush();
  }

  function styleChanged() {
    const style = styleAt(); if (!style) return;
    Object.assign(style, {
      fontFamily: refs.fontFamily.value, fontWeight: Number(refs.fontWeight.value), textColor: refs.textColor.value,
      shadow: refs.textShadow.checked, uppercase: refs.uppercase.checked,
      italic: refs.italic.checked, outline: refs.textOutline.checked, background: refs.textBackground.checked,
      x: Number(refs.positionX.value), y: Number(refs.positionY.value), maxWidth: Number(refs.maxWidth.value),
      lineHeight: Number(refs.lineHeight.value), letterSpacing: Number(refs.letterSpacing.value)
    });
    refs.textColorValue.textContent = style.textColor.toUpperCase();
    refs.positionXOut.value = `${style.x}%`; refs.positionYOut.value = `${style.y}%`; refs.maxWidthOut.value = `${style.maxWidth}%`;
    refs.lineHeightOut.value = style.lineHeight.toFixed(2); refs.letterSpacingOut.value = `${style.letterSpacing} px`;
    renderPreview(); saveSettings(); scheduleVisualPush();
  }

  function restoreCurrentStyle() {
    const [section, component] = app.styleTarget.split(".");
    const original = app.defaults.styles?.[section]?.[component];
    if (!original) return;
    app.state.styles[section][component] = clone(original);
    applyStyleControls(); renderPreview(); saveSettings(); scheduleVisualPush();
    toast("Estilo restaurado", refs.styleTarget.selectedOptions[0]?.textContent || "Elemento");
  }

  function applyUiSettings() {
    const ui = app.settings.ui || {};
    document.documentElement.style.setProperty("--blue", ui.accentColor || "#1687ff");
    document.body.dataset.density = ui.density || "comfortable";
    const scale = Number(ui.scale || 100) / 100;
    const shell = $(".app-shell"); shell.style.zoom = String(scale); shell.style.width = `${100 / scale}%`; shell.style.height = `${100 / scale}vh`;
  }

  function applySettingsControls() {
    const ui = app.settings.ui || {};
    refs.uiAccent.value = ui.accentColor || "#1687ff"; refs.uiScale.value = ui.scale || 100; refs.uiScaleOut.value = `${ui.scale || 100}%`;
    refs.uiDensity.value = ui.density || "comfortable"; refs.confirmDelete.checked = ui.confirmDelete !== false; refs.confirmClear.checked = Boolean(ui.confirmClear);
    refs.crossfadeMs.value = app.settings.videoCrossfadeMs ?? 450; refs.crossfadeOut.value = `${app.settings.videoCrossfadeMs ?? 450} ms`;
    refs.previewMode.value = app.settings.performance?.previewMode || "frame";
    refs.ljaPath.value = app.settings.louvorJaDb || "";
    refs.screenFill.checked = app.settings.output?.openFullscreenSize !== false;
    const clock = app.settings.clock || {};
    refs.clock24.checked = clock.format24 !== false; refs.clockSeconds.checked = Boolean(clock.showSeconds);
    refs.clockShowDate.checked = clock.showDate !== false; refs.clockDateFormat.value = clock.dateFormat || "long"; refs.clockLabel.value = clock.label || "";
    refs.fontAutoImport.checked = app.settings.fonts?.autoImport !== false;
    const youtube = app.settings.youtube || {};
    refs.ytDefaultHeight.value = String(youtube.defaultHeight || 720);
    refs.ytAutoDownload.checked = youtube.autoDownload !== false;
    refs.ytAutoSwitch.checked = youtube.autoSwitchToFile !== false;
    const bible = app.settings.bible || {};
    refs.bibleShowVersion.checked = bible.showVersion !== false; refs.bibleReferenceFormat.value = bible.referenceFormat || "full";
    const song = app.settings.song || {};
    refs.songShowLabels.checked = song.showSectionLabels !== false; refs.songShowCredits.checked = Boolean(song.showCredits); refs.songCreditsFormat.value = song.creditsFormat || "artist";
    applyUiSettings();
  }

  function songSettingsChanged() {
    app.settings.song = {
      ...(app.settings.song || {}), showSectionLabels: refs.songShowLabels.checked,
      showCredits: refs.songShowCredits.checked, creditsFormat: refs.songCreditsFormat.value
    };
    refreshSongDeckOptions();
  }

  function generalSettingsChanged() {
    app.settings.ui = {
      ...(app.settings.ui || {}), accentColor: refs.uiAccent.value, scale: Number(refs.uiScale.value),
      density: refs.uiDensity.value, confirmDelete: refs.confirmDelete.checked, confirmClear: refs.confirmClear.checked
    };
    app.settings.performance = { ...(app.settings.performance || {}), previewMode: refs.previewMode.value };
    app.settings.output = { ...(app.settings.output || {}), openFullscreenSize: refs.screenFill.checked };
    app.settings.videoCrossfadeMs = Number(refs.crossfadeMs.value);
    refs.uiScaleOut.value = `${app.settings.ui.scale}%`; refs.crossfadeOut.value = `${app.settings.videoCrossfadeMs} ms`;
    applyUiSettings(); renderPreview(); saveSettings();
  }

  function applyThemeControls() {
    syncStyleEditor();
  }

  function themeChanged() {
    styleChanged();
  }

  function scheduleVisualPush() {
    if (!app.state.live) return;
    clearTimeout(app.visualTimer);
    app.visualTimer = setTimeout(() => pushState(buildVisualState(true)), 75);
  }

  function saveSettings() {
    clearTimeout(app.settingsTimer);
    app.settingsTimer = setTimeout(() => {
      app.settings.theme = app.state.theme; app.settings.styles = app.state.styles; app.settings.clock = clockDraft();
      app.settings.bible = { ...(app.settings.bible || {}), showVersion: refs.bibleShowVersion.checked, referenceFormat: refs.bibleReferenceFormat.value };
      app.settings.defaultBackground = app.state.background; app.settings.defaultOverlay = app.state.overlay;
      api("/api/settings", { method: "POST", body: JSON.stringify(app.settings) }).catch(() => {});
    }, 350);
  }

  function updateClockPreview() {
    const content = formatClockContent(clockDraft());
    refs.clockPreview.textContent = content.text;
    refs.clockDate.textContent = content.reference;
    const monitorState = app.state && (app.monitorView === "draft" ? buildDraftPreviewState() : app.state);
    if (monitorState?.mode === "clock") renderMonitorPreview();
  }

  function clockDraftChanged() {
    app.draftMode = "clock";
    if (app.state.live && app.state.mode === "clock") {
      app.state.clock = clockDraft();
      app.monitorView = "output";
      scheduleVisualPush();
    } else {
      app.monitorView = "draft";
    }
    updateClockPreview();
    renderPreview(); syncStyleEditor(); saveSettings();
  }

  function presentClock() {
    app.draftMode = "clock";
    app.monitorView = "output";
    pushState(buildClockState(true));
  }

  function copyText(text, message) {
    navigator.clipboard.writeText(text).then(() => toast(message)).catch(() => prompt("Copie o texto:", text));
  }

  async function refreshLjaStatus() {
    refs.ljaStatusTitle.textContent = "Verificando…"; refs.ljaStatusDot.className = "status-dot";
    try {
      app.ljaStatus = await api("/api/louvorja/status");
      refs.ljaStatusDot.className = `status-dot ${app.ljaStatus.available ? "ready" : "error"}`;
      refs.ljaStatusTitle.textContent = app.ljaStatus.available ? `Conectado • ${app.ljaStatus.count} músicas` : "Louvor JA não encontrado";
      refs.ljaStatusDetail.textContent = app.ljaStatus.available ? app.ljaStatus.path : app.ljaStatus.message;
      refs.ljaQuickStatus.textContent = app.ljaStatus.available ? `${app.ljaStatus.count} músicas • funciona offline` : "Clique para configurar";
      refs.ljaDialogStatus.textContent = app.ljaStatus.available ? `${app.ljaStatus.count} músicas disponíveis. O banco será usado somente para leitura.` : app.ljaStatus.message;
      try {
        app.ljaBibleStatus = await api("/api/louvorja/bible/status");
        app.ljaBibles = app.ljaBibleStatus.available ? app.ljaBibleStatus.versions : [];
        refs.ljaBibleQuickStatus.textContent = app.ljaBibleStatus.available
          ? `${app.ljaBibleStatus.count} versões • 66 livros • offline`
          : app.ljaBibleStatus.message;
      } catch (bibleError) {
        app.ljaBibles = [];
        refs.ljaBibleQuickStatus.textContent = bibleError.message;
      }
      renderBibles();
      restoreBibleOnce();
    } catch (error) {
      refs.ljaStatusDot.className = "status-dot error"; refs.ljaStatusTitle.textContent = "Falha na verificação"; refs.ljaStatusDetail.textContent = error.message;
      refs.ljaQuickStatus.textContent = "Não foi possível verificar";
      refs.ljaBibleQuickStatus.textContent = "Não foi possível verificar";
    }
  }

  async function saveLjaPath() {
    app.settings.louvorJaDb = refs.ljaPath.value.trim();
    try {
      app.settings = await api("/api/settings", { method: "POST", body: JSON.stringify({ louvorJaDb: app.settings.louvorJaDb }) });
      await refreshLjaStatus(); toast("Caminho do Louvor JA salvo");
    } catch (error) { toast("Não foi possível salvar", error.message); }
  }

  async function searchLja() {
    const query = refs.ljaQuery.value.trim(); if (query.length < 2) return;
    refs.ljaResults.innerHTML = '<div class="dialog-empty">Pesquisando no catálogo local…</div>';
    try {
      const results = await api(`/api/louvorja/search?q=${encodeURIComponent(query)}`);
      refs.ljaResults.replaceChildren();
      if (!results.length) { refs.ljaResults.innerHTML = '<div class="dialog-empty">Nenhuma música encontrada.</div>'; return; }
      const importedIds = new Set(app.songs.filter(song => song.source === "Louvor JA").map(song => String(song.sourceId)));
      results.forEach(result => {
        const row = document.createElement("div"); row.className = "online-result";
        const meta = document.createElement("div"); const title = document.createElement("b"); title.textContent = result.title;
        const detail = document.createElement("small"); detail.textContent = result.albums.join(" • ") || "Louvor JA"; meta.append(title, detail);
        const button = document.createElement("button"); button.type = "button";
        const imported = importedIds.has(String(result.id)); button.textContent = imported ? "NA BIBLIOTECA" : "IMPORTAR"; button.classList.toggle("imported", imported);
        button.addEventListener("click", async () => {
          button.disabled = true; button.textContent = "…";
          try {
            const response = await api("/api/louvorja/import", { method: "POST", body: JSON.stringify({ id: result.id }) });
            let song = response.song;
            if (!response.alreadyImported) app.songs.push(song);
            else song = app.songs.find(item => item.id === song.id) || song;
            renderSongs(); selectSong(song); refs.ljaDialog.close();
            toast(response.alreadyImported ? "Música já estava na biblioteca" : "Letra importada do Louvor JA", song.title);
          } catch (error) { toast("Falha ao importar", error.message); button.disabled = false; button.textContent = imported ? "NA BIBLIOTECA" : "IMPORTAR"; }
        });
        row.append(meta, button); refs.ljaResults.append(row);
      });
    } catch (error) { refs.ljaResults.innerHTML = `<div class="dialog-empty">${String(error.message).replace(/[<>]/g, "")}</div>`; }
  }

  function uploadFont(file) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest(); xhr.open("POST", "/api/font/upload"); xhr.setRequestHeader("X-Filename", encodeURIComponent(file.name));
      xhr.onerror = () => reject(new Error("Falha de rede durante o envio"));
      xhr.onload = () => { let payload = {}; try { payload = JSON.parse(xhr.responseText); } catch (_) {} if (xhr.status >= 200 && xhr.status < 300) resolve(payload); else reject(new Error(payload.error || `Erro ${xhr.status}`)); };
      xhr.send(file);
    });
  }

  async function importFontFile(file) {
    if (!file) return;
    try {
      const font = await uploadFont(file); app.fonts.push(font); app.state.fonts = app.fonts;
      renderFontFaces(); populateFontOptions(); refs.fontFamily.value = `"${font.family}"`; styleChanged();
      if (app.state.live) pushState(buildVisualState(true));
      toast("Fonte instalada no NexStage", font.name);
    } catch (error) { toast("Não foi possível importar a fonte", error.message); }
  }

  function fontSyncSummary(result) {
    const added = (result.imported?.length || 0) + (result.updated?.length || 0);
    const removed = result.removedManual?.length || 0;
    const kept = result.keptManual?.length || 0;
    if (!result.found) return "Nenhuma fonte CMG encontrada no sistema";
    const parts = [`${result.found} no sistema`];
    if (added) parts.push(`${added} importada${added === 1 ? "" : "s"}`);
    if (removed) parts.push(`${removed} manual${removed === 1 ? "" : "is"} removida${removed === 1 ? "" : "s"}`);
    if (kept) parts.push(`${kept} manual${kept === 1 ? "" : "is"} mantida${kept === 1 ? "" : "s"}`);
    return parts.join(" • ");
  }

  async function syncSystemFonts() {
    refs.fontSyncNow.disabled = true; refs.fontSyncStatus.textContent = "Procurando…";
    try {
      const result = await api("/api/fonts/sync", { method: "POST", body: "{}" });
      app.fonts = result.fonts || []; app.state.fonts = app.fonts;
      if (result.removedManual?.length && result.styles) {
        // cópias manuais apagadas: os estilos passam a usar a fonte do sistema
        app.settings.styles = clone(result.styles); app.state.styles = clone(result.styles);
        applyStyleControls();
      }
      renderFontFaces(); populateFontOptions();
      if (app.state.live) pushState(buildVisualState(true));
      refs.fontSyncStatus.textContent = fontSyncSummary(result);
      toast("Fontes CMG", fontSyncSummary(result));
    } catch (error) {
      refs.fontSyncStatus.textContent = "Não foi possível verificar";
      toast("Falha ao procurar fontes", error.message);
    } finally { refs.fontSyncNow.disabled = false; }
  }

  function fontAutoImportChanged() {
    app.settings.fonts = { ...(app.settings.fonts || {}), autoImport: refs.fontAutoImport.checked };
    saveSettings();
  }

  // ---- YouTube: controle remoto (o vídeo só toca na projeção; aqui não há player) ----
  function ytFormatTime(value) {
    const total = Math.max(0, Math.floor(Number(value) || 0));
    const h = Math.floor(total / 3600), m = Math.floor((total % 3600) / 60), sec = total % 60;
    return h ? `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}` : `${m}:${String(sec).padStart(2, "0")}`;
  }

  function ytActiveTab() { return $(".tab-panel.active")?.dataset.panel === "youtube"; }

  async function ytRefresh() {
    try { app.yt = await api("/api/youtube"); renderYoutube(); } catch (_) { /* servidor reiniciando */ }
  }
  function ytStartPolling() { clearInterval(app.ytTimer); ytRefresh(); app.ytTimer = setInterval(ytRefresh, 600); }
  function ytStopPolling() { clearInterval(app.ytTimer); app.ytTimer = null; }

  async function ytCommand(action, extra = {}) {
    try {
      const result = await api("/api/youtube/command", { method: "POST", body: JSON.stringify({ action, ...extra }) });
      app.state = result.state;
      if (app.yt) app.yt.status = result.status;
      updateLiveUi(); renderPreview(); renderYoutube();
    } catch (error) { toast("YouTube", error.message); }
  }

  async function ytAddVideo(text) {
    const value = String(text ?? refs.ytInput.value).trim();
    if (!value) return;
    refs.ytAdd.disabled = true;
    try {
      await api("/api/youtube/add", { method: "POST", body: JSON.stringify({ text: value }) });
      refs.ytInput.value = "";
      toast("Vídeo adicionado", "Buscando informações e baixando em segundo plano.");
      await ytRefresh();
    } catch (error) { toast("Não foi possível adicionar", error.message); }
    finally { refs.ytAdd.disabled = false; }
  }

  function ytHeightsOf(id) { return (app.yt?.items || []).find(item => item.id === id)?.heights || [360, 480, 720, 1080]; }

  function ytRenderTools(data) {
    const tools = data.tools || {}, install = tools.install || {};
    const signature = JSON.stringify([tools.ready, tools.ffmpeg, install.state, install.message, Math.floor((install.percent || 0) / 4)]);
    if (signature === app.ytToolsSignature) return;
    app.ytToolsSignature = signature;
    const box = refs.ytTools;
    if (tools.ready && install.state !== "running" && install.state !== "error") { box.hidden = true; box.replaceChildren(); return; }
    box.hidden = false; box.className = `yt-tools${install.state === "error" ? " error" : ""}`;
    const text = document.createElement("div");
    const button = document.createElement("button"); button.className = "button soft"; button.type = "button";
    if (install.state === "running") {
      text.textContent = `${install.message || "Instalando"} (${install.percent || 0}%)`;
      const bar = document.createElement("div"); bar.className = "bar"; const fill = document.createElement("i"); fill.style.width = `${install.percent || 0}%`; bar.append(fill);
      box.replaceChildren(text, bar); return;
    }
    if (install.state === "error") text.textContent = install.message || "Falha ao instalar os componentes.";
    else if (!tools.ffmpeg) text.textContent = "O ffmpeg não foi encontrado neste computador. Reinstale o NexStage.";
    else text.textContent = "Para usar o YouTube, o NexStage baixa dois componentes uma única vez (cerca de 60 MB). Precisa de internet agora; depois os vídeos já baixados funcionam sem internet.";
    button.textContent = install.state === "error" ? "Tentar de novo" : "Instalar agora";
    button.addEventListener("click", async () => { await api("/api/youtube/install", { method: "POST", body: "{}" }).catch(error => toast("YouTube", error.message)); ytRefresh(); });
    box.replaceChildren(text, ...(tools.ffmpeg || install.state === "error" ? [button] : []));
  }

  function ytJobPercent(item, height) { return item.jobs?.[String(height)]?.percent ?? 0; }

  function ytBuildRow(item) {
    const row = document.createElement("div"); row.className = "yt-item"; row.dataset.id = item.id;
    const image = document.createElement("img"); image.alt = ""; image.loading = "lazy"; image.referrerPolicy = "no-referrer"; image.src = item.thumbnail || "";
    image.addEventListener("error", () => { image.style.visibility = "hidden"; });
    const meta = document.createElement("div"); meta.className = "yt-meta";
    const title = document.createElement("b"); title.textContent = item.title || item.id;
    const sub = document.createElement("small");
    if (item.info === "pending") sub.textContent = "Buscando informações…";
    else if (item.info === "needs-tools") sub.textContent = "Aguardando a instalação dos componentes.";
    else if (item.info === "error") { sub.textContent = item.error || "Não foi possível ler este vídeo."; sub.className = "bad"; }
    else sub.textContent = [item.channel, item.duration ? ytFormatTime(item.duration) : ""].filter(Boolean).join(" • ");
    meta.append(title, sub);
    if (item.info === "ok") {
      const chips = document.createElement("div"); chips.className = "yt-chips";
      (item.heights || []).forEach(height => {
        const chip = document.createElement("span"); chip.className = "yt-chip";
        const job = item.jobs?.[String(height)];
        if (item.files?.[String(height)]) { chip.classList.add("done"); chip.textContent = `${height}p ✓`; chip.title = "Baixado: toca do arquivo"; }
        else if (job && (job.state === "queued" || job.state === "running")) {
          chip.classList.add("busy"); chip.title = "Baixando";
          chip.append(`${height}p `); const pct = document.createElement("span"); pct.dataset.pct = `${item.id}:${height}`; pct.textContent = job.state === "queued" ? "na fila" : `${job.percent || 0}%`; chip.append(pct);
        } else {
          chip.textContent = `${height}p ⬇`; chip.title = job?.state === "error" ? `Falhou: ${job.error}. Clique para tentar de novo.` : "Clique para baixar esta resolução";
          chip.addEventListener("click", async () => { await api("/api/youtube/download", { method: "POST", body: JSON.stringify({ id: item.id, height }) }).catch(error => toast("Download", error.message)); ytRefresh(); });
        }
        chips.append(chip);
      });
      meta.append(chips);
    }
    const actions = document.createElement("div"); actions.className = "yt-actions";
    if (item.info === "ok" || Object.keys(item.files || {}).length) {
      const play = document.createElement("button"); play.className = "button primary"; play.type = "button"; play.textContent = "Projetar";
      play.addEventListener("click", () => ytCommand("load", { id: item.id }));
      actions.append(play);
    } else if (item.info === "error" || item.info === "needs-tools") {
      const retry = document.createElement("button"); retry.className = "button soft"; retry.type = "button"; retry.textContent = "Tentar de novo";
      retry.addEventListener("click", () => ytAddVideo(item.id));
      actions.append(retry);
    }
    const remove = document.createElement("button"); remove.className = "button ghost icon"; remove.type = "button"; remove.title = "Remover da lista e apagar o arquivo"; remove.append(makeIcon("i-trash"));
    remove.addEventListener("click", async () => {
      if (!confirm(`Remover "${item.title || item.id}" e apagar os arquivos baixados?`)) return;
      await api("/api/youtube/remove", { method: "POST", body: JSON.stringify({ id: item.id }) }).catch(error => toast("YouTube", error.message)); ytRefresh();
    });
    actions.append(remove); meta.append(actions);
    row.append(image, meta);
    return row;
  }

  function ytRenderList(data) {
    const items = data.items || [];
    refs.ytCount.textContent = String(items.length);
    // A estrutura só é refeita quando algo muda de verdade; a porcentagem é atualizada no lugar (cliques não se perdem).
    const structure = JSON.stringify(items.map(item => [item.id, item.title, item.info, item.error, item.heights, Object.keys(item.files || {}), Object.entries(item.jobs || {}).map(([h, j]) => [h, j.state])]));
    if (structure !== app.ytListSignature) {
      app.ytListSignature = structure;
      if (!items.length) {
        const empty = document.createElement("div"); empty.className = "empty-state";
        const bold = document.createElement("b"); bold.textContent = "Nenhum vídeo ainda";
        const hint = document.createElement("span"); hint.textContent = "Cole um link do YouTube (ou só o código de 11 letras) acima.";
        empty.append(bold, hint); refs.ytList.replaceChildren(empty);
      } else refs.ytList.replaceChildren(...items.map(ytBuildRow));
    }
    items.forEach(item => Object.entries(item.jobs || {}).forEach(([height, job]) => {
      const node = refs.ytList.querySelector(`[data-pct="${item.id}:${height}"]`);
      if (node) node.textContent = job.state === "queued" ? "na fila" : `${job.percent || 0}%`;
    }));
    refs.ytList.querySelectorAll(".yt-item").forEach(row => row.classList.toggle("playing", row.dataset.id === data.status?.item));
  }

  function ytRenderRemote(data) {
    const status = data.status || {};
    const hasVideo = Boolean(status.item);
    const duration = Number(status.duration || 0);
    refs.ytNowTitle.textContent = hasVideo ? (status.title || status.item) : "Nenhum vídeo na projeção";
    let info = "Adicione um vídeo e clique em Projetar.", tone = "";
    if (hasVideo) {
      const item = (data.items || []).find(entry => entry.id === status.item);
      const job = item?.jobs?.[String(status.height)];
      if (!status.connected) { info = "A projeção não está respondendo. Abra o telão (botão no topo)."; tone = "warn"; }
      else if (status.error) { info = status.error; tone = "bad"; }
      else if (status.needsGesture) { info = "Clique uma vez na tela da projeção para liberar o som."; tone = "warn"; }
      else {
        const parts = [status.mode === "stream" ? "Transmissão direta" : "Arquivo local", `${status.height}p`];
        if (status.mode === "stream" && job && (job.state === "running" || job.state === "queued")) parts.push(`baixando ${job.percent || 0}%`);
        parts.push(status.buffering ? "carregando…" : status.ended ? "terminou" : status.playing ? "tocando" : "pausado");
        info = parts.join(" • ");
      }
    }
    refs.ytNowInfo.textContent = info; refs.ytNowInfo.className = tone;
    [refs.ytBack, refs.ytFwd, refs.ytPlay, refs.ytStop].forEach(button => { button.disabled = !hasVideo; });
    refs.ytSeek.disabled = !hasVideo || !duration;
    if (!app.ytDragging) refs.ytSeek.value = String(duration ? Math.round(Math.min(1, (status.t || 0) / duration) * 1000) : 0);
    if (!app.ytDragging) refs.ytTime.textContent = ytFormatTime(status.t || 0);
    refs.ytDur.textContent = ytFormatTime(duration);
    const playing = Boolean(status.wantPlaying) && !status.ended;
    refs.ytPlay.textContent = status.ended ? "Repetir" : playing ? "Pausar" : "Reproduzir";
    refs.ytPlay.classList.toggle("pausing", playing);
    if (typeof status.volume === "number") {
      if (Date.now() - (app.ytVolumeHold || 0) > 900) refs.ytVolume.value = String(Math.round(status.volume * 100));
      refs.ytVolText.textContent = `${status.muted ? 0 : Math.round(status.volume * 100)}%`;
      app.settings.youtube = { ...(app.settings.youtube || {}), volume: status.volume };
    }
    refs.ytMute.classList.toggle("on", Boolean(status.muted)); refs.ytMute.textContent = status.muted ? "Mudo ligado" : "Mudo";
    const item = (data.items || []).find(entry => entry.id === status.item);
    const heights = item?.heights?.length ? item.heights : [360, 480, 720, 1080];
    const quality = JSON.stringify([status.item, status.height, heights, Object.keys(item?.files || {})]);
    if (quality !== app.ytQualitySignature) {
      app.ytQualitySignature = quality;
      refs.ytQuality.replaceChildren(...heights.map(height => { const o = new Option(`${height}p${item?.files?.[String(height)] ? "  ✓ baixado" : ""}`, String(height)); return o; }));
      if (!heights.length) refs.ytQuality.replaceChildren(new Option("—", ""));
      refs.ytQuality.value = String(status.height || "");
    }
    refs.ytQuality.disabled = !hasVideo;
  }

  function renderYoutube() {
    const data = app.yt;
    if (!data) return;
    ytRenderTools(data); ytRenderList(data); ytRenderRemote(data);
  }

  function ytHandleKey(event) {
    if (event.ctrlKey || event.altKey || event.metaKey) return false;
    const status = app.yt?.status || {};
    if (event.key === " ") { event.preventDefault(); ytCommand("toggle"); return true; }
    if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
      event.preventDefault(); ytCommand("seek", { delta: (event.key === "ArrowRight" ? 1 : -1) * (event.shiftKey ? 30 : 5) }); return true;
    }
    if (event.key === "ArrowUp" || event.key === "ArrowDown") {
      event.preventDefault(); app.ytVolumeHold = Date.now();
      ytCommand("volume", { value: Math.max(0, Math.min(1, (status.volume ?? 0.8) + (event.key === "ArrowUp" ? 0.05 : -0.05))) }); return true;
    }
    if (event.key.toLowerCase() === "m") { event.preventDefault(); ytCommand("mute", { value: !status.muted }); return true; }
    return false;
  }

  function wireYoutube() {
    refs.ytAdd.addEventListener("click", () => ytAddVideo());
    refs.ytInput.addEventListener("keydown", event => { if (event.key === "Enter") { event.preventDefault(); ytAddVideo(); } });
    refs.ytInput.addEventListener("paste", () => setTimeout(() => { if (/^(https?:\/\/|www\.|youtu)/i.test(refs.ytInput.value.trim())) ytAddVideo(); }, 0));
    refs.ytPlay.addEventListener("click", () => ytCommand("toggle"));
    refs.ytBack.addEventListener("click", () => ytCommand("seek", { delta: -10 }));
    refs.ytFwd.addEventListener("click", () => ytCommand("seek", { delta: 10 }));
    refs.ytStop.addEventListener("click", () => ytCommand("stop"));
    refs.ytMute.addEventListener("click", () => ytCommand("mute", { value: !app.yt?.status?.muted }));
    refs.ytQuality.addEventListener("change", () => ytCommand("quality", { height: Number(refs.ytQuality.value) }));
    refs.ytSeek.addEventListener("input", () => {
      app.ytDragging = true;
      refs.ytTime.textContent = ytFormatTime((Number(refs.ytSeek.value) / 1000) * Number(app.yt?.status?.duration || 0));
    });
    refs.ytSeek.addEventListener("change", async () => {
      const target = (Number(refs.ytSeek.value) / 1000) * Number(app.yt?.status?.duration || 0);
      await ytCommand("seek", { t: target });
      app.ytDragging = false; refs.ytSeek.blur();
    });
    refs.ytVolume.addEventListener("input", () => {
      app.ytVolumeHold = Date.now();
      refs.ytVolText.textContent = `${refs.ytVolume.value}%`;
      clearTimeout(app.ytVolumeTimer);
      const wait = Math.max(0, 120 - (Date.now() - (app.ytVolumeLast || 0)));
      app.ytVolumeTimer = setTimeout(() => { app.ytVolumeLast = Date.now(); ytCommand("volume", { value: Number(refs.ytVolume.value) / 100 }); }, wait);
    });
    refs.ytVolume.addEventListener("change", () => refs.ytVolume.blur());
    const saveYoutubeOptions = () => {
      app.settings.youtube = { ...(app.settings.youtube || {}), defaultHeight: Number(refs.ytDefaultHeight.value), autoDownload: refs.ytAutoDownload.checked, autoSwitchToFile: refs.ytAutoSwitch.checked };
      saveSettings();
    };
    [refs.ytDefaultHeight, refs.ytAutoDownload, refs.ytAutoSwitch].forEach(control => control.addEventListener("change", saveYoutubeOptions));
    refs.ytUpdateTools.addEventListener("click", async () => {
      try { await api("/api/youtube/install", { method: "POST", body: JSON.stringify({ update: true }) }); toast("YouTube", "Atualizando os componentes…"); ytRefresh(); }
      catch (error) { toast("YouTube", error.message); }
    });
  }

  function downloadJson(filename, payload) {
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob); const link = document.createElement("a");
    link.href = url; link.download = filename; document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  async function exportSettingsFile() {
    try {
      const bundle = await api("/api/settings/export");
      downloadJson(`NexStage-configuracoes-${bundle.appVersion || "0.5.1"}.nxsconfig`, bundle);
      toast("Configurações exportadas", "O arquivo foi salvo na pasta de downloads.");
    } catch (error) { toast("Não foi possível exportar", error.message); }
  }

  async function importSettingsFile(file) {
    if (!file) return;
    try {
      const bundle = JSON.parse(await readTextSmart(file));
      if (!confirm("Aplicar estas configurações? Seus ajustes visuais atuais serão substituídos.")) return;
      await api("/api/settings/import", { method: "POST", body: JSON.stringify(bundle) });
      toast("Configurações importadas", "Recarregando a interface…");
      setTimeout(() => location.reload(), 650);
    } catch (error) {
      toast("Arquivo de configurações inválido", error.message);
    } finally {
      refs.settingsInput.value = "";
    }
  }

  function openSlideEditor(index) {
    const slide = app.deck[index]; if (!slide || !app.selectedSongId) return;
    const song = app.songs.find(item => item.id === app.selectedSongId); if (!song) return;
    app.editingSlide = index; refs.slideDialogTitle.textContent = `Slide ${index + 1} de ${app.deckTitle}`;
    refs.slideLabel.value = slide.sectionLabel ?? slide.label ?? ""; refs.slideText.value = slide.text || "";
    refs.songEditTitle.value = song.title || ""; refs.songEditArtist.value = song.artist || ""; refs.songEditAlbum.value = song.album || "";
    refs.slideDialog.showModal();
    setTimeout(() => refs.slideText.focus(), 50);
  }

  async function persistSongDeck() {
    const song = app.songs.find(item => item.id === app.selectedSongId); if (!song) return;
    try {
      const updated = await api("/api/song/update", { method: "POST", body: JSON.stringify({
        ...song,
        title: refs.songEditTitle.value.trim() || song.title,
        artist: refs.songEditArtist.value.trim(),
        album: refs.songEditAlbum.value.trim(),
        slides: app.deck.map(slide => ({ text: slide.text, label: slide.sectionLabel ?? slide.label ?? "" }))
      }) });
      Object.assign(song, updated); app.deckTitle = song.title; refs.currentTitle.textContent = song.title; refs.slidesTitle.textContent = song.title;
      refreshSongDeckOptions(); renderSongs();
    } catch (error) { toast("Não foi possível salvar a letra", error.message); }
  }

  function commitSlideFields() {
    const slide = app.deck[app.editingSlide]; if (!slide) return false;
    const text = refs.slideText.value.trim(); if (!text) { toast("O slide precisa ter texto"); return false; }
    slide.text = text; slide.sectionLabel = refs.slideLabel.value.trim();
    slide.label = app.settings.song?.showSectionLabels === false ? "" : slide.sectionLabel;
    return true;
  }

  async function saveSlideEditor() {
    if (!commitSlideFields()) return; refs.slideDialog.close(); await persistSongDeck(); toast("Slide atualizado");
  }

  async function splitSlideAtCursor() {
    const position = refs.slideText.selectionStart; const text = refs.slideText.value;
    let split = position > 0 && position < text.length ? position : text.indexOf("\n", Math.floor(text.length / 2));
    if (split <= 0 || split >= text.length) { toast("Posicione o cursor onde deseja dividir"); return; }
    const first = text.slice(0, split).trim(); const second = text.slice(split).trim(); if (!first || !second) return;
    const sectionLabel = refs.slideLabel.value.trim(); const label = app.settings.song?.showSectionLabels === false ? "" : sectionLabel;
    app.deck.splice(app.editingSlide, 1, { text: first, label, sectionLabel, reference: songCredit(app.songs.find(item => item.id === app.selectedSongId)) }, { text: second, label, sectionLabel, reference: songCredit(app.songs.find(item => item.id === app.selectedSongId)) });
    refs.slideDialog.close(); await persistSongDeck(); toast("Slide dividido");
  }

  async function duplicateEditingSlide() {
    if (!commitSlideFields()) return; app.deck.splice(app.editingSlide + 1, 0, clone(app.deck[app.editingSlide])); refs.slideDialog.close(); await persistSongDeck(); toast("Slide duplicado");
  }

  async function deleteEditingSlide() {
    if (app.deck.length <= 1) { toast("A música precisa ter pelo menos um slide"); return; }
    app.deck.splice(app.editingSlide, 1); app.currentIndex = Math.min(app.currentIndex, app.deck.length - 1); refs.slideDialog.close(); await persistSongDeck(); toast("Slide excluído");
  }

  function screenKey(screen) {
    return [screen.label || "Tela", screen.width, screen.height, screen.isInternal ? "I" : "E", screen.isPrimary ? "P" : "S"].join("|");
  }

  function renderScreens() {
    refs.screenSelect.replaceChildren(new Option("Automático / atual", ""));
    app.screens.forEach((screen, index) => {
      const kind = screen.isInternal ? "interna" : "externa"; const primary = screen.isPrimary ? " • principal" : "";
      refs.screenSelect.add(new Option(`${index + 1}. ${screen.label || `Monitor ${index + 1}`} — ${screen.width}×${screen.height} (${kind}${primary})`, screenKey(screen)));
    });
    const saved = app.settings.output?.preferredScreen || "";
    if ([...refs.screenSelect.options].some(option => option.value === saved)) refs.screenSelect.value = saved;
  }

  async function detectScreens(quiet = false) {
    if (!("getScreenDetails" in window)) {
      refs.screenHelp.textContent = "Este navegador não permite escolher o monitor automaticamente. O telão abrirá normalmente.";
      if (!quiet) toast("Seleção automática indisponível", "Use Chrome ou Edge atualizado, ou mova a janela manualmente.");
      return;
    }
    try {
      app.screenDetails = await window.getScreenDetails(); app.screens = [...app.screenDetails.screens]; renderScreens();
      refs.screenHelp.textContent = `${app.screens.length} monitor${app.screens.length === 1 ? "" : "es"} detectado${app.screens.length === 1 ? "" : "s"}.`;
      if (!app.screenEventsBound) {
        app.screenDetails.addEventListener("screenschange", () => { app.screens = [...app.screenDetails.screens]; renderScreens(); });
        app.screenEventsBound = true;
      }
      if (!quiet) toast("Monitores atualizados", refs.screenHelp.textContent);
    } catch (error) {
      refs.screenHelp.textContent = "Permissão de monitores não concedida. O modo manual continua disponível.";
      if (!quiet) toast("Não foi possível detectar", error.message);
    }
  }

  async function restoreScreensIfAllowed() {
    if (!("getScreenDetails" in window) || !("permissions" in navigator)) return;
    try {
      const permission = await navigator.permissions.query({ name: "window-management" });
      if (permission.state === "granted") await detectScreens(true);
    } catch (_) { /* Navegadores antigos usam apenas a seleção manual. */ }
  }

  function focusVisualEditor(mode, target) {
    app.draftMode = mode; app.visualEditorMode = mode; app.monitorView = "draft"; syncStyleEditor(target); renderPreview();
    refs.styleTarget.focus(); refs.styleTarget.scrollIntoView({ behavior: "smooth", block: "center" });
    toast("Editor visual pronto", "Você também pode arrastar o elemento diretamente na prévia grande.");
  }

  function openOutputWindow() {
    const key = refs.screenSelect.value; const screen = app.screens.find(item => screenKey(item) === key);
    let width = 1280, height = 720, left, top;
    if (screen) {
      if (refs.screenFill.checked) { width = screen.availWidth; height = screen.availHeight; left = screen.availLeft; top = screen.availTop; }
      else { width = Math.min(1280, screen.availWidth); height = Math.min(720, screen.availHeight); left = screen.availLeft + Math.max(0, (screen.availWidth - width) / 2); top = screen.availTop + Math.max(0, (screen.availHeight - height) / 2); }
    }
    const features = [`popup=yes`, `width=${Math.round(width)}`, `height=${Math.round(height)}`];
    if (Number.isFinite(left)) features.push(`left=${Math.round(left)}`, `top=${Math.round(top)}`);
    const output = window.open("/output", "nexstage_output", features.join(","));
    if (!output) { toast("O navegador bloqueou a janela", "Permita pop-ups para o endereço local do NexStage."); return; }
    if (screen) setTimeout(() => { try { output.moveTo(left, top); output.resizeTo(width, height); output.focus(); } catch (_) {} }, 350);
  }

  function targetForPreviewKind(kind) {
    const mode = app.visualEditorMode || (app.draftMode === "bible" ? "bible" : "song");
    if (mode === "clock") return `clock.${kind === "text" ? "time" : kind === "reference" ? "date" : "label"}`;
    if (mode === "bible") return `bible.${kind === "text" ? "text" : kind === "reference" ? "reference" : "version"}`;
    return `song.${kind}`;
  }

  function startPreviewDrag(event) {
    const kind = event.currentTarget.dataset.kind; if (!kind) return;
    syncStyleEditor(targetForPreviewKind(kind)); app.drag = { pointerId: event.pointerId, element: event.currentTarget };
    event.currentTarget.setPointerCapture?.(event.pointerId); movePreviewDrag(event); event.preventDefault();
  }

  function movePreviewDrag(event) {
    if (!app.drag || app.drag.pointerId !== event.pointerId) return;
    const bounds = refs.previewFrame.getBoundingClientRect(); const style = styleAt(); if (!style) return;
    style.x = Math.max(0, Math.min(100, Math.round((event.clientX - bounds.left) / bounds.width * 100)));
    style.y = Math.max(0, Math.min(100, Math.round((event.clientY - bounds.top) / bounds.height * 100)));
    refs.positionX.value = style.x; refs.positionY.value = style.y; refs.positionXOut.value = `${style.x}%`; refs.positionYOut.value = `${style.y}%`;
    renderPreview(); scheduleVisualPush();
  }

  function endPreviewDrag(event) {
    if (!app.drag || app.drag.pointerId !== event.pointerId) return; app.drag = null; saveSettings();
  }

  function wireEvents() {
    $$(".rail-button").forEach(button => button.addEventListener("click", () => switchTab(button.dataset.tab)));
    refs.songFilter.addEventListener("input", renderSongs);
    $("#importTxt").addEventListener("click", () => refs.txtInput.click()); refs.txtInput.addEventListener("change", event => importTxtFiles(event.target.files));
    $("#importBible").addEventListener("click", () => refs.bibleInput.click()); refs.bibleInput.addEventListener("change", event => importBibleFile(event.target.files[0]));
    $("#importMedia").addEventListener("click", () => refs.mediaInput.click()); refs.mediaDrop.addEventListener("click", () => refs.mediaInput.click()); refs.mediaInput.addEventListener("change", event => handleMediaFiles(event.target.files));
    ["dragenter", "dragover"].forEach(type => refs.mediaDrop.addEventListener(type, event => { event.preventDefault(); refs.mediaDrop.classList.add("drag"); }));
    ["dragleave", "drop"].forEach(type => refs.mediaDrop.addEventListener(type, event => { event.preventDefault(); refs.mediaDrop.classList.remove("drag"); }));
    refs.mediaDrop.addEventListener("drop", event => handleMediaFiles(event.dataTransfer.files));
    refs.bibleSelect.addEventListener("change", () => bibleChanged()); refs.bookSelect.addEventListener("change", bookChanged); refs.chapterSelect.addEventListener("change", chapterChanged);
    refs.verseSelect.addEventListener("change", verseChanged); refs.verseToSelect.addEventListener("change", applyBibleSelection); refs.bibleJoin.addEventListener("change", applyBibleSelection);
    refs.bibleQuick.addEventListener("input", bibleQuickPreview);
    refs.bibleQuick.addEventListener("keydown", event => { if (event.key === "Enter") { event.preventDefault(); event.stopPropagation(); bibleQuickGo(); } });
    refs.bibleQuickGo.addEventListener("click", bibleQuickGo);
    refs.biblePrevChapter.addEventListener("click", () => stepBibleChapter(-1));
    refs.bibleNextChapter.addEventListener("click", () => stepBibleChapter(1));
    refs.bibleShowVersion.addEventListener("change", bibleSettingsChanged); refs.bibleReferenceFormat.addEventListener("change", bibleSettingsChanged);
    refs.songShowLabels.addEventListener("change", songSettingsChanged); refs.songShowCredits.addEventListener("change", songSettingsChanged); refs.songCreditsFormat.addEventListener("change", songSettingsChanged);
    $("#editBibleVisual").addEventListener("click", () => focusVisualEditor("bible", "bible.text"));
    $("#editClockVisual").addEventListener("click", () => focusVisualEditor("clock", "clock.time"));

    $("#openOnline").addEventListener("click", () => { refs.onlineDialog.showModal(); setTimeout(() => refs.onlineQuery.focus(), 80); });
    refs.onlineDialog.querySelector(".dialog-close").addEventListener("click", () => refs.onlineDialog.close());
    $("#searchOnline").addEventListener("click", searchOnline); refs.onlineQuery.addEventListener("keydown", event => { if (event.key === "Enter") searchOnline(); });

    $("#openLouvorJA").addEventListener("click", async () => { refs.ljaDialog.showModal(); await refreshLjaStatus(); setTimeout(() => refs.ljaQuery.focus(), 80); });
    refs.ljaDialog.querySelector(".lja-close").addEventListener("click", () => refs.ljaDialog.close());
    $("#searchLja").addEventListener("click", searchLja); refs.ljaQuery.addEventListener("keydown", event => { if (event.key === "Enter") searchLja(); });
    $("#saveLjaPath").addEventListener("click", saveLjaPath); $("#refreshLja").addEventListener("click", refreshLjaStatus);

    wireYoutube();
    refs.fontSyncNow.addEventListener("click", syncSystemFonts); refs.fontAutoImport.addEventListener("change", fontAutoImportChanged);
    $("#importFont").addEventListener("click", () => refs.fontInput.click()); refs.fontInput.addEventListener("change", event => importFontFile(event.target.files[0]));
    $("#refreshLjaBibles").addEventListener("click", async () => { await refreshLjaStatus(); toast(app.ljaBibleStatus?.available ? "Bíblias atualizadas" : "Bíblias indisponíveis", refs.ljaBibleQuickStatus.textContent); });
    $("#exportSettings").addEventListener("click", exportSettingsFile);
    $("#importSettings").addEventListener("click", () => refs.settingsInput.click());
    refs.settingsInput.addEventListener("change", event => importSettingsFile(event.target.files[0]));
    refs.checkUpdates.addEventListener("click", () => checkForUpdates(false, true));
    refs.updatePill.addEventListener("click", () => switchTab("settings"));
    refs.installUpdate.addEventListener("click", installAvailableUpdate);
    refs.openDataFolder.addEventListener("click", async () => {
      try {
        await api("/api/system/open-data", { method: "POST", body: "{}" });
      } catch (error) {
        toast("Não foi possível abrir a pasta", error.message);
      }
    });
    $("#detectScreens").addEventListener("click", () => detectScreens(false));
    refs.screenSelect.addEventListener("change", () => { app.settings.output = { ...(app.settings.output || {}), preferredScreen: refs.screenSelect.value }; saveSettings(); });
    $("#openOutput").addEventListener("click", openOutputWindow);

    const obsAddress = `${location.origin}/obs`;
    refs.obsUrl.textContent = obsAddress;
    [$("#copyObs"), $("#copyObsSettings")].forEach(button => button.addEventListener("click", () => copyText(obsAddress, "Endereço do OBS copiado")));
    $("#copyCss").addEventListener("click", () => copyText(`#lyrics {\n  font-family: Arial, sans-serif !important;\n  font-size: 64px !important;\n  left: 50% !important;\n  top: 72% !important;\n  width: 88% !important;\n}\n#reference { color: #66b7ff !important; }\n#church-overlay { right: 3% !important; bottom: 4% !important; }`, "CSS de exemplo copiado"));
    $("#backgroundPicker").addEventListener("click", () => { app.pickerMode = "background"; switchTab("media"); toast("Escolha o fundo", "Clique em uma mídia da biblioteca"); });
    $("#overlayPicker").addEventListener("click", () => { app.pickerMode = "overlay"; switchTab("media"); toast("Escolha a logo", "Clique em uma imagem da biblioteca"); });
    $("#clearBackground").addEventListener("click", () => { app.state.background = ""; renderMedia(); renderPreview(); saveSettings(); if (app.state.live) pushState(buildVisualState(true)); });
    $("#clearOverlay").addEventListener("click", () => { app.state.overlay = ""; renderMedia(); renderPreview(); saveSettings(); if (app.state.live) pushState(buildVisualState(true)); });

    refs.styleTarget.addEventListener("change", () => { app.styleTarget = refs.styleTarget.value; applyStyleControls(); });
    refs.fontSize.addEventListener("input", () => fontSizeChanged("range"));
    refs.fontSizeNumber.addEventListener("input", () => { if (Number(refs.fontSizeNumber.value) > 0) fontSizeChanged("number"); });
    refs.fontSizeNumber.addEventListener("change", () => { if (Number(refs.fontSizeNumber.value) > 0) fontSizeChanged("number"); else applyStyleControls(); });
    [refs.textColor, refs.positionX, refs.positionY, refs.maxWidth, refs.lineHeight, refs.letterSpacing].forEach(control => control.addEventListener("input", styleChanged));
    [refs.fontFamily, refs.fontWeight, refs.textShadow, refs.uppercase, refs.italic, refs.textOutline, refs.textBackground].forEach(control => control.addEventListener("change", styleChanged));
    $$("[data-align]").forEach(button => button.addEventListener("click", () => {
      const style = styleAt(); if (!style) return; style.align = button.dataset.align;
      $$("[data-align]").forEach(item => item.classList.toggle("active", item === button)); renderPreview(); saveSettings(); scheduleVisualPush();
    }));
    $("#restoreStyle").addEventListener("click", restoreCurrentStyle);
    [refs.previewLabel, refs.previewText, refs.previewReference].forEach(element => {
      element.addEventListener("pointerdown", startPreviewDrag); element.addEventListener("pointermove", movePreviewDrag);
      element.addEventListener("pointerup", endPreviewDrag); element.addEventListener("pointercancel", endPreviewDrag);
    });

    [refs.uiAccent, refs.uiScale, refs.crossfadeMs].forEach(control => control.addEventListener("input", generalSettingsChanged));
    [refs.uiDensity, refs.confirmDelete, refs.confirmClear, refs.previewMode, refs.screenFill].forEach(control => control.addEventListener("change", generalSettingsChanged));
    $("#clearFrameCache").addEventListener("click", () => { app.videoFrameCache.clear(); refs.previewBg.dataset.source = ""; refs.stagePreviewBg.dataset.source = ""; renderPreview(); toast("Cache de frames limpo"); });

    $$("[data-monitor-view]").forEach(button => button.addEventListener("click", () => setMonitorView(button.dataset.monitorView)));
    refs.goLive.addEventListener("click", () => { if (app.draftMode === "clock") presentClock(); else if (app.deck.length) { app.monitorView = "output"; pushState(buildLyricsState(true)); } else toast("Escolha o que apresentar", "Selecione um slide ou abra o relógio."); });
    refs.blackout.addEventListener("click", () => { app.monitorView = "output"; pushState({ ...app.state, black: !app.state.black }); });
    $("#clearOutput").addEventListener("click", () => { if (app.settings.ui?.confirmClear && !confirm("Limpar a saída do telão?")) return; app.monitorView = "output"; pushState({ ...app.state, live: false, black: false }); });
    $("#previousSlide").addEventListener("click", () => stepSlide(-1));
    $("#nextSlide").addEventListener("click", () => stepSlide(1));
    $("#presentClock").addEventListener("click", presentClock);
    [refs.clock24, refs.clockSeconds, refs.clockShowDate, refs.clockDateFormat].forEach(control => control.addEventListener("change", clockDraftChanged)); refs.clockLabel.addEventListener("input", clockDraftChanged);

    refs.slideDialog.querySelector(".slide-close").addEventListener("click", () => refs.slideDialog.close());
    $("#saveSlide").addEventListener("click", saveSlideEditor); $("#splitSlide").addEventListener("click", splitSlideAtCursor);
    $("#duplicateSlide").addEventListener("click", duplicateEditingSlide); $("#deleteSlide").addEventListener("click", deleteEditingSlide);

    addEventListener("keydown", event => {
      if (/INPUT|SELECT|TEXTAREA/.test(event.target.tagName) || refs.onlineDialog.open || refs.ljaDialog.open || refs.slideDialog.open) return;
      if (ytActiveTab() && app.yt?.status?.item && ytHandleKey(event)) return;
      if (event.key === "/" && !event.ctrlKey && !event.altKey && !event.metaKey) { event.preventDefault(); switchTab("bible"); refs.bibleQuick.focus(); refs.bibleQuick.select(); return; }
      if ((event.key === "ArrowRight" || event.key === "ArrowLeft") && event.shiftKey && app.draftMode === "bible" && app.bibleChapter) {
        event.preventDefault(); stepBibleChapter(event.key === "ArrowRight" ? 1 : -1, { present: true }); return;
      }
      if (event.key === "ArrowRight") { event.preventDefault(); stepSlide(1); }
      if (event.key === "ArrowLeft") { event.preventDefault(); stepSlide(-1); }
      if (event.key === "Enter") { event.preventDefault(); if (app.draftMode === "clock") presentClock(); else if (app.deck.length) { app.monitorView = "output"; pushState(buildLyricsState(true)); } }
      if (event.key === "Escape") { app.monitorView = "output"; pushState({ ...app.state, live: false, black: false }); }
      if (event.key.toLowerCase() === "b") { app.monitorView = "output"; pushState({ ...app.state, black: !app.state.black }); }
    });
    addEventListener("resize", renderPreview);
  }

  async function init() {
    try {
      const data = await api("/api/bootstrap");
      Object.assign(app, { songs: data.songs, bibles: data.bibles, media: data.media, fonts: data.fonts || [], defaults: data.defaults || {}, settings: data.settings, state: data.state });
      app.state.theme = { ...data.settings.theme, ...data.state.theme };
      app.state.styles = app.state.styles || clone(data.settings.styles || data.defaults?.styles || {}); app.state.fonts = app.fonts;
      app.draftMode = app.state.mode === "clock" ? "clock" : app.state.mode === "bible" ? "bible" : "song";
      app.monitorView = app.state.live || app.state.black ? "output" : "draft";
      applySettingsControls(); renderFontFaces(); populateFontOptions(); renderScreens();
      renderSongs(); renderBibles(); renderMedia(); renderSlides(); applyThemeControls(); renderPreview(); updateLiveUi(); updateClockPreview(); wireEvents();
      refreshLjaStatus(); restoreScreensIfAllowed();
      if (data.fontSync && Object.keys(data.fontSync).length) {
        refs.fontSyncStatus.textContent = fontSyncSummary(data.fontSync);
        if (data.fontSync.announce && (data.fontSync.imported?.length || 0) + (data.fontSync.updated?.length || 0) + (data.fontSync.removedManual?.length || 0)) toast("Fontes CMG", fontSyncSummary(data.fontSync));
      } else refs.fontSyncStatus.textContent = app.settings.fonts?.autoImport === false ? "Importação automática desligada" : "Ainda não verificado";
      await loadAbout();
      if (app.appInfo?.updateSupported) setTimeout(() => checkForUpdates(true), 1800);
      setInterval(updateClockPreview, 500);
    } catch (error) {
      document.body.innerHTML = `<main style="font:16px system-ui;padding:40px;color:white"><h1>NexStage não iniciou</h1><p>${String(error.message).replace(/[<>]/g, "")}</p></main>`;
    }
  }

  init();
})();

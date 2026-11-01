(() => {
  "use strict";

  const body = document.body;
  const isObs = body.dataset.output === "obs";
  const showObsBackground = isObs && new URLSearchParams(location.search).get("background") === "1";
  if (showObsBackground) body.classList.add("obs-background");

  const elements = {
    slots: [document.getElementById("mediaA"), document.getElementById("mediaB")],
    content: document.getElementById("content"),
    label: document.getElementById("label"),
    lyrics: document.getElementById("lyrics"),
    reference: document.getElementById("reference"),
    overlay: document.getElementById("church-overlay"),
    blackout: document.getElementById("blackout"),
    fullscreen: document.getElementById("fullscreenHint")
  };

  const yt = {
    el: document.getElementById("ytVideo"), token: -1, seekToken: 0, mode: "", startAt: 0, duration: 0,
    ended: false, error: "", needsGesture: false, buffering: false, wantMuted: false, bgPaused: false, loading: false
  };
  const obsAudio = new URLSearchParams(location.search).get("audio") === "1";

  let revision = 0;
  let activeSlot = 0;
  let backgroundUrl = null;
  let backgroundToken = 0;
  let clockTimer = null;
  let currentState = null;
  let fontSignature = "";

  function applyFontFaces(fonts = []) {
    const signature = JSON.stringify(fonts.map(font => [font.family, font.url, font.format]));
    if (signature === fontSignature) return;
    fontSignature = signature;
    let style = document.getElementById("nexstage-fonts");
    if (!style) {
      style = document.createElement("style");
      style.id = "nexstage-fonts";
      document.head.append(style);
    }
    style.textContent = fonts.map(font =>
      `@font-face{font-family:"${String(font.family).replaceAll('"', '')}";src:url("${String(font.url).replaceAll('"', '%22')}") format("${font.format || 'truetype'}");font-display:swap;}`
    ).join("\n");
  }

  function mediaKind(url) {
    const path = String(url || "").split("?")[0].toLowerCase();
    return /\.(mp4|webm|mov|m4v)$/.test(path) ? "video" : "image";
  }

  function waitForMedia(media, eventName, timeout = 2600) {
    return new Promise(resolve => {
      let finished = false;
      const done = () => {
        if (finished) return;
        finished = true;
        media.removeEventListener(eventName, done);
        resolve();
      };
      media.addEventListener(eventName, done, { once: true });
      setTimeout(done, timeout);
    });
  }

  async function setBackground(url, crossfadeMs = 450) {
    if (isObs && !showObsBackground) return;
    url = url || "";
    if (url === backgroundUrl) return;
    backgroundUrl = url;
    const token = ++backgroundToken;
    const nextIndex = 1 - activeSlot;
    const next = elements.slots[nextIndex];
    const previous = elements.slots[activeSlot];
    next.style.transitionDuration = `${Math.max(0, crossfadeMs)}ms`;
    previous.style.transitionDuration = `${Math.max(0, crossfadeMs)}ms`;
    next.classList.remove("active");
    next.replaceChildren();

    if (url) {
      if (mediaKind(url) === "video") {
        const video = document.createElement("video");
        video.muted = true;
        video.loop = true;
        video.autoplay = true;
        video.playsInline = true;
        video.preload = "auto";
        video.disablePictureInPicture = true;
        video.src = url;
        next.append(video);
        video.load();
        await waitForMedia(video, "canplay");
        if (token !== backgroundToken) {
          video.pause();
          return;
        }
        if (!yt.bgPaused) { try { await video.play(); } catch (_) { /* autoplay is muted; retry occurs on visibility */ } }
      } else {
        const image = document.createElement("img");
        image.alt = "";
        image.src = url;
        next.append(image);
        if (image.decode) {
          try { await image.decode(); } catch (_) { /* broken file shows the fallback */ }
        } else {
          await waitForMedia(image, "load");
        }
      }
    }

    if (token !== backgroundToken) return;
    requestAnimationFrame(() => {
      next.classList.add("active");
      previous.classList.remove("active");
    });
    activeSlot = nextIndex;
    setTimeout(() => {
      if (activeSlot === nextIndex) {
        previous.querySelector("video")?.pause();
        previous.replaceChildren();
      }
    }, Math.max(0, crossfadeMs) + 120);
  }

  function hexRgba(hex, opacity) {
    const value = String(hex || "#000000").replace("#", "");
    const full = value.length === 3 ? value.split("").map(part => part + part).join("") : value;
    const number = Number.parseInt(full, 16);
    if (!Number.isFinite(number)) return `rgba(0,0,0,${opacity})`;
    return `rgba(${number >> 16},${(number >> 8) & 255},${number & 255},${opacity})`;
  }

  function legacyStyle(theme = {}, overrides = {}) {
    return {
      fontFamily: theme.fontFamily || "Arial, Helvetica, sans-serif",
      fontSize: theme.fontSize || 64,
      fontWeight: theme.fontWeight || 800,
      textColor: theme.textColor || "#ffffff",
      align: theme.align || "center",
      x: 50, y: 50, maxWidth: theme.maxWidth || 86,
      lineHeight: 1.13, letterSpacing: 0,
      shadow: theme.shadow !== false, uppercase: Boolean(theme.uppercase),
      italic: false, outline: false, background: false,
      backgroundColor: "#000000", backgroundOpacity: .35,
      autoFit: true, minFontSize: 26,
      ...overrides
    };
  }

  function stylesForState(state) {
    const all = state.styles || {};
    const theme = state.theme || {};
    if (state.mode === "clock") {
      return {
        label: all.clock?.label || legacyStyle(theme, { fontSize: 26, y: 27 }),
        lyrics: all.clock?.time || legacyStyle(theme, { fontSize: 112, fontWeight: 300, y: 50 }),
        reference: all.clock?.date || legacyStyle(theme, { fontSize: 28, y: 72 })
      };
    }
    if (state.mode === "bible") {
      return {
        label: all.bible?.version || legacyStyle(theme, { fontSize: 22, y: 20 }),
        lyrics: all.bible?.text || legacyStyle(theme, { fontSize: 58, y: 48 }),
        reference: all.bible?.reference || legacyStyle(theme, { fontSize: 28, y: 79 })
      };
    }
    return {
      label: all.song?.label || legacyStyle(theme, { fontSize: 24, y: 24 }),
      lyrics: all.song?.text || legacyStyle(theme),
      reference: all.song?.reference || legacyStyle(theme, { fontSize: 24, y: 80 })
    };
  }

  function applyBlockStyle(element, style = {}) {
    const scale = Math.max(0.42, innerHeight / 1080);
    element.style.left = `${Number(style.x ?? 50)}%`;
    element.style.top = `${Number(style.y ?? 50)}%`;
    element.style.width = `${Number(style.maxWidth ?? 86)}%`;
    element.style.fontFamily = style.fontFamily || "Arial, Helvetica, sans-serif";
    element.style.fontSize = `${Math.max(5, Number(style.fontSize || 64) * scale)}px`;
    element.style.fontWeight = String(style.fontWeight || 400);
    element.style.color = style.textColor || "#ffffff";
    element.style.textAlign = style.align || "center";
    element.style.lineHeight = String(style.lineHeight || 1.13);
    element.style.letterSpacing = `${Number(style.letterSpacing || 0) * scale}px`;
    element.style.textTransform = style.uppercase ? "uppercase" : "none";
    element.style.fontStyle = style.italic ? "italic" : "normal";
    element.style.textShadow = style.shadow === false ? "none" : "0 .06em .2em #000, 0 .02em .04em #000, 0 0 .4em #0008";
    element.style.webkitTextStroke = style.outline ? `${Math.max(1, 1.5 * scale)}px #000` : "0 transparent";
    element.style.background = style.background ? hexRgba(style.backgroundColor, Number(style.backgroundOpacity ?? .35)) : "transparent";
    element.style.padding = style.background ? `${8 * scale}px ${14 * scale}px` : "0";
    element.style.borderRadius = style.background ? `${8 * scale}px` : "0";
  }

  function setTheme(state) {
    const styles = stylesForState(state);
    applyBlockStyle(elements.label, styles.label);
    applyBlockStyle(elements.lyrics, styles.lyrics);
    applyBlockStyle(elements.reference, styles.reference);
    document.documentElement.style.setProperty("--overlay-opacity", String(state.theme?.overlayOpacity ?? 1));
  }

  function formatClock(state) {
    const options = {
      hour: "2-digit",
      minute: "2-digit",
      second: state.clock?.showSeconds ? "2-digit" : undefined,
      hour12: state.clock?.format24 === false
    };
    elements.lyrics.textContent = new Intl.DateTimeFormat("pt-BR", options).format(new Date());
    elements.label.textContent = state.clock?.label || "";
    if (state.clock?.showDate === false) {
      elements.reference.textContent = "";
    } else if (state.clock?.dateFormat === "short") {
      elements.reference.textContent = new Intl.DateTimeFormat("pt-BR").format(new Date());
    } else if (state.clock?.dateFormat === "weekday") {
      elements.reference.textContent = new Intl.DateTimeFormat("pt-BR", { weekday: "long" }).format(new Date());
    } else {
      elements.reference.textContent = new Intl.DateTimeFormat("pt-BR", {
        weekday: "long", day: "2-digit", month: "long"
      }).format(new Date());
    }
  }

  function startClock(state) {
    clearInterval(clockTimer);
    formatClock(state);
    clockTimer = setInterval(() => formatClock(currentState || state), 250);
  }

  function stopClock() {
    clearInterval(clockTimer);
    clockTimer = null;
  }

  function fitText() {
    if (currentState?.mode === "clock") return;
    const style = stylesForState(currentState).lyrics;
    const scale = Math.max(0.55, innerHeight / 1080);
    let size = Math.round((style.fontSize || 64) * scale);
    const min = Math.round((style.minFontSize || 26) * scale);
    const maxHeight = innerHeight * 0.67;
    elements.lyrics.style.fontSize = `${size}px`;
    if (style.autoFit === false) return;
    const overflows = () => {
      return elements.lyrics.scrollHeight > maxHeight || elements.lyrics.scrollWidth > elements.lyrics.clientWidth + 2;
    };
    while (overflows() && size > min) {
      size -= 2;
      elements.lyrics.style.fontSize = `${size}px`;
    }
  }

  // ---- YouTube ---------------------------------------------------------
  // The operator panel sends commands; this page only plays and reports its position.
  function ytPosition() {
    const base = yt.mode === "stream" ? yt.startAt : 0;
    return base + (Number.isFinite(yt.el.currentTime) ? yt.el.currentTime : 0);
  }

  function ytUnload() {
    if (yt.token === -1 && !yt.el.getAttribute("src")) return;
    yt.token = -1;
    yt.el.pause();
    yt.el.removeAttribute("src");
    yt.el.load();
    yt.el.classList.remove("visible");
    yt.ended = false; yt.error = ""; yt.needsGesture = false; yt.buffering = false;
  }

  function ytLoad(y) {
    yt.token = y.srcToken;
    yt.mode = y.mode;
    yt.startAt = Number(y.startAt || 0);
    yt.duration = Number(y.duration || 0);
    yt.seekToken = y.seekToken;
    yt.ended = false; yt.error = ""; yt.buffering = true; yt.loading = true;
    yt.el.pause();
    yt.el.src = y.src;
    yt.el.load();
  }

  function ytPlay() {
    const attempt = yt.el.play();
    if (!attempt || !attempt.catch) return;
    attempt.catch(error => {
      if (error && error.name === "NotAllowedError") {
        // Sound blocked until the first click on this page: play silently meanwhile.
        yt.needsGesture = true;
        yt.el.muted = true;
        yt.el.play().catch(() => {});
      }
    });
  }

  function applyYoutube(state) {
    const y = state.youtube || {};
    const hasVideo = Boolean(y.item && y.src && state.mode === "youtube");
    const visible = hasVideo && Boolean(state.live && !state.black);
    document.body.classList.toggle("mode-youtube", visible);
    if (!hasVideo) {
      ytUnload();
    } else {
      if (y.srcToken !== yt.token) ytLoad(y);
      if (y.seekToken !== yt.seekToken) {
        yt.seekToken = y.seekToken;
        if (y.mode === "file") { yt.ended = false; try { yt.el.currentTime = Number(y.seekTo || 0); } catch (_) { /* not ready yet */ } }
      }
      yt.wantMuted = Boolean(y.muted) || (isObs && !obsAudio);
      yt.el.volume = Math.max(0, Math.min(1, Number(y.volume ?? 1)));
      yt.el.muted = yt.wantMuted || yt.needsGesture;
      yt.el.classList.toggle("visible", visible);
      if (visible && y.playing && !yt.ended) { if (yt.el.paused) ytPlay(); }
      else if (!yt.el.paused) yt.el.pause();
    }
    // Only one thing decodes at a time: the looping background video rests while the YouTube video is on screen.
    if (visible !== yt.bgPaused) {
      yt.bgPaused = visible;
      document.querySelectorAll(".media-slot video").forEach(video => { if (visible) video.pause(); else video.play().catch(() => {}); });
    }
  }

  yt.el.addEventListener("loadedmetadata", () => {
    yt.loading = false;
    if (yt.mode === "file" && yt.startAt > 0.5) { try { yt.el.currentTime = yt.startAt; } catch (_) { /* ignored */ } }
  });
  yt.el.addEventListener("waiting", () => { yt.buffering = true; });
  yt.el.addEventListener("stalled", () => { yt.buffering = true; });
  yt.el.addEventListener("playing", () => { yt.buffering = false; yt.error = ""; });
  yt.el.addEventListener("canplay", () => { yt.buffering = false; });
  yt.el.addEventListener("ended", () => { yt.ended = true; });
  yt.el.addEventListener("error", () => {
    const code = yt.el.error?.code;
    yt.error = code === 4 ? "O navegador não conseguiu abrir este vídeo (arquivo ou transmissão indisponível)." : "Erro ao reproduzir o vídeo.";
    yt.buffering = false;
  });

  // First click on the projection allows sound (browsers block sound until the page was used once).
  document.addEventListener("pointerdown", () => {
    if (yt.needsGesture) { yt.needsGesture = false; yt.el.muted = yt.wantMuted; }
  }, true);

  if (!isObs) {
    setInterval(() => {
      if (yt.token === -1) return;
      const payload = {
        srcToken: yt.token, t: ytPosition(), duration: yt.duration || (Number.isFinite(yt.el.duration) ? yt.el.duration : 0),
        playing: !yt.el.paused && !yt.el.ended, buffering: yt.buffering || (yt.el.readyState < 3 && !yt.el.paused),
        ended: yt.ended, error: yt.error, needsGesture: yt.needsGesture
      };
      fetch("/api/youtube/report", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload), cache: "no-store" }).catch(() => {});
    }, 500);
  }

  function applyState(state) {
    currentState = state;
    revision = Number(state.revision || revision);
    applyFontFaces(state.fonts || []);
    setTheme(state);
    setBackground(state.background, state.videoCrossfadeMs || 450);

    const isClock = state.mode === "clock";
    body.classList.toggle("mode-clock", isClock);
    if (isClock) {
      if (!clockTimer) startClock(state); else formatClock(state);
    } else {
      stopClock();
      elements.label.textContent = state.slide?.label || "";
      elements.lyrics.textContent = state.slide?.text || "";
      elements.reference.textContent = state.slide?.reference || "";
    }

    const visible = Boolean(state.live && !state.black && state.mode !== "youtube" && (isClock || state.slide?.text));
    elements.content.classList.toggle("visible", visible);

    const overlayVisible = Boolean(state.overlay && !state.black);
    if (state.overlay && elements.overlay.getAttribute("src") !== state.overlay) {
      elements.overlay.src = state.overlay;
    }
    elements.overlay.classList.toggle("visible", overlayVisible);
    applyYoutube(state);

    // A black OBS browser source would cover the camera. In OBS, blackout means transparency.
    elements.blackout.classList.toggle("visible", Boolean(state.black && !isObs));
    requestAnimationFrame(fitText);
  }

  async function poll() {
    for (;;) {
      try {
        const response = await fetch(`/api/state?since=${revision}`, { cache: "no-store" });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        applyState(await response.json());
      } catch (_) {
        await new Promise(resolve => setTimeout(resolve, 900));
      }
    }
  }

  function requestFullscreen() {
    document.documentElement.requestFullscreen?.().then(() => {
      if (elements.fullscreen) elements.fullscreen.hidden = true;
    }).catch(() => {});
  }

  elements.fullscreen?.addEventListener("click", requestFullscreen);
  document.addEventListener("dblclick", () => { if (!isObs) requestFullscreen(); });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden && !yt.bgPaused) elements.slots[activeSlot].querySelector("video")?.play().catch(() => {});
  });
  addEventListener("resize", () => { if (currentState) { setTheme(currentState); fitText(); } });
  poll();
})();

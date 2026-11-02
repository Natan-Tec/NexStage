/* NexStage - interpretador de referências bíblicas digitadas (ex.: "jo 3:16", "1co 13:4-7").
   Sem dependências. Funciona no navegador (window.NexBibleRef) e no Node (module.exports) para testes. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.NexBibleRef = api;
})(typeof self !== "undefined" ? self : this, function () {
  // Abreviações usuais em português, na ordem tradicional dos 66 livros.
  const PT_ABBR = [
    "gn", "ex", "lv", "nm", "dt", "js", "jz", "rt", "1sm", "2sm", "1rs", "2rs", "1cr", "2cr", "ed", "ne", "et", "jó", "sl", "pv",
    "ec", "ct", "is", "jr", "lm", "ez", "dn", "os", "jl", "am", "ob", "jn", "mq", "na", "hc", "sf", "ag", "zc", "ml",
    "mt", "mc", "lc", "jo", "at", "rm", "1co", "2co", "gl", "ef", "fp", "cl", "1ts", "2ts", "1tm", "2tm", "tt", "fm", "hb", "tg",
    "1pe", "2pe", "1jo", "2jo", "3jo", "jd", "ap"
  ];

  function stripAccents(text) {
    return String(text || "").normalize("NFD").replace(/[̀-ͯ]/g, "");
  }

  // Chave de comparação: sem acento, minúscula, números romanos/ordinais viram dígitos, sem espaços ou pontos.
  function bookKey(name) {
    let text = stripAccents(name).toLowerCase().trim();
    text = text
      .replace(/^(iii|3|terceir[oa])\b\.?\s*/, "3")
      .replace(/^(ii|2|segund[oa])\b\.?\s*/, "2")
      .replace(/^(i|1|primeir[oa])\b\.?\s*/, "1");
    return text.replace(/[^a-z0-9]/g, "");
  }

  // Versão que preserva acentos, para separar "Jó" de "Jo" (João) quando o usuário acentua.
  function accentKey(name) {
    return String(name || "").toLowerCase().replace(/[\s.\-]/g, "");
  }

  function parse(text) {
    const value = String(text || "").trim().replace(/[–—]/g, "-");
    if (!value) return null;
    const match = value.match(/^(.*?)(?:\s*(\d{1,3})\s*(?:[:.,]|\s)\s*(\d{1,3})(?:\s*-\s*(\d{1,3}))?|\s*(\d{1,3}))?$/);
    if (!match) return null;
    const book = (match[1] || "").trim();
    if (!book || !/[a-zA-ZÀ-ÿ]/.test(book)) return null;
    const chapter = Number(match[2] || match[5] || 1);
    const verse = match[3] ? Number(match[3]) : 0;
    let to = match[4] ? Number(match[4]) : 0;
    if (!verse || to <= verse) to = 0;
    if (!chapter) return null;
    return { book, chapter, verse, to };
  }

  // books: [{ name, abbreviation }]. Retorna a posição na lista ou -1.
  function findBook(query, books) {
    const q = bookKey(query);
    if (!q || !Array.isArray(books) || !books.length) return -1;
    const raw = accentKey(query);
    const useTable = books.length === 66;
    const entries = books.map((book, index) => {
      const names = [book.name];
      const abbreviations = [book.abbreviation, useTable ? PT_ABBR[index] : ""];
      return {
        index,
        nameKey: bookKey(book.name),
        abbrKeys: abbreviations.filter(Boolean).map(bookKey).filter(Boolean),
        rawKeys: names.concat(abbreviations).filter(Boolean).map(accentKey)
      };
    });
    const pick = (list, last = false) => (list.length ? (last ? list[list.length - 1] : list[0]).index : -1);

    // 1) igual, respeitando acentos (jó ≠ jo)
    let found = pick(entries.filter(item => item.rawKeys.includes(raw)), true);
    if (found >= 0) return found;
    // "jo" sem acento é João (Jó só quando acentuado), mesmo em Bíblias sem abreviações
    if (q === "jo" && raw === "jo") {
      found = pick(entries.filter(item => item.nameKey === "joao"));
      if (found >= 0) return found;
    }
    // 2) igual, sem acentos (em empate prefere o Novo Testamento: "jo" = João)
    found = pick(entries.filter(item => item.nameKey === q || item.abbrKeys.includes(q)), true);
    if (found >= 0) return found;
    // 3) começa com o que foi digitado
    found = pick(entries.filter(item => item.nameKey.startsWith(q)));
    if (found >= 0) return found;
    found = pick(entries.filter(item => item.abbrKeys.some(key => key.startsWith(q))));
    if (found >= 0) return found;
    // 4) contém (só com 3+ letras)
    if (q.length >= 3) {
      found = pick(entries.filter(item => item.nameKey.includes(q)));
      if (found >= 0) return found;
    }
    // 5) último recurso (Bíblias sem abreviações): letras na ordem, começando pela mesma letra ("sl" → Salmos)
    if (q.length >= 2 && /^[0-9]?[a-z]+$/.test(q)) {
      const inOrder = key => {
        if (key[0] !== q[0]) return false;
        let at = 0;
        for (const letter of q) { at = key.indexOf(letter, at); if (at < 0) return false; at += 1; }
        return true;
      };
      return pick(entries.filter(item => inOrder(item.nameKey)));
    }
    return -1;
  }

  // Interpreta o texto inteiro. Retorna { pos, chapter, verse, to } ou null.
  function resolve(text, books) {
    const parsed = parse(text);
    if (!parsed) return null;
    const pos = findBook(parsed.book, books);
    if (pos < 0) return null;
    return { pos, chapter: parsed.chapter, verse: parsed.verse, to: parsed.to };
  }

  return { parse, findBook, resolve, bookKey, PT_ABBR };
});

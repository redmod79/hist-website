/**
 * Bible Reference Popup System
 * - Verse references: Genesis 1:1, John 3:16, etc.
 * - Strong's numbers: H430, G5590, etc.
 */

(function() {
  // Book name normalization
  const bookMap = {
    'genesis': 'Gen', 'gen': 'Gen',
    'exodus': 'Exo', 'exo': 'Exo', 'exod': 'Exo',
    'leviticus': 'Lev', 'lev': 'Lev',
    'numbers': 'Num', 'num': 'Num',
    'deuteronomy': 'Deu', 'deut': 'Deu', 'deu': 'Deu',
    'joshua': 'Jos', 'josh': 'Jos',
    'judges': 'Jdg', 'judg': 'Jdg',
    'ruth': 'Rth',
    '1 samuel': '1Sa', '1 sam': '1Sa',
    '2 samuel': '2Sa', '2 sam': '2Sa',
    '1 kings': '1Ki', '2 kings': '2Ki',
    '1 chronicles': '1Ch', '1 chron': '1Ch',
    '2 chronicles': '2Ch', '2 chron': '2Ch',
    'ezra': 'Ezr',
    'nehemiah': 'Neh', 'neh': 'Neh',
    'esther': 'Est', 'est': 'Est',
    'job': 'Job',
    'psalm': 'Psa', 'psalms': 'Psa', 'psa': 'Psa', 'ps': 'Psa',
    'proverbs': 'Pro', 'prov': 'Pro', 'pro': 'Pro',
    'ecclesiastes': 'Ecc', 'eccl': 'Ecc', 'ecc': 'Ecc',
    'song of solomon': 'Sng', 'song': 'Sng',
    'isaiah': 'Isa', 'isa': 'Isa',
    'jeremiah': 'Jer', 'jer': 'Jer',
    'lamentations': 'Lam', 'lam': 'Lam',
    'ezekiel': 'Ezk', 'ezek': 'Ezk', 'eze': 'Ezk',
    'daniel': 'Dan', 'dan': 'Dan',
    'hosea': 'Hos', 'hos': 'Hos',
    'joel': 'Jol',
    'amos': 'Amo',
    'obadiah': 'Oba', 'obad': 'Oba',
    'jonah': 'Jon', 'jon': 'Jon',
    'micah': 'Mic', 'mic': 'Mic',
    'nahum': 'Nah', 'nah': 'Nah',
    'habakkuk': 'Hab', 'hab': 'Hab',
    'zephaniah': 'Zep', 'zeph': 'Zep',
    'haggai': 'Hag', 'hag': 'Hag',
    'zechariah': 'Zec', 'zech': 'Zec', 'zec': 'Zec',
    'malachi': 'Mal', 'mal': 'Mal',
    'matthew': 'Mat', 'matt': 'Mat', 'mat': 'Mat',
    'mark': 'Mrk', 'mrk': 'Mrk',
    'luke': 'Luk', 'luk': 'Luk',
    'john': 'Jhn', 'jhn': 'Jhn',
    'acts': 'Act',
    'romans': 'Rom', 'rom': 'Rom',
    '1 corinthians': '1Co', '1 cor': '1Co',
    '2 corinthians': '2Co', '2 cor': '2Co',
    'galatians': 'Gal', 'gal': 'Gal',
    'ephesians': 'Eph', 'eph': 'Eph',
    'philippians': 'Php', 'phil': 'Php', 'php': 'Php',
    'colossians': 'Col', 'col': 'Col',
    '1 thessalonians': '1Th', '1 thess': '1Th', '1 th': '1Th',
    '2 thessalonians': '2Th', '2 thess': '2Th', '2 th': '2Th',
    '1 timothy': '1Ti', '1 tim': '1Ti',
    '2 timothy': '2Ti', '2 tim': '2Ti',
    'titus': 'Tit', 'tit': 'Tit',
    'philemon': 'Phm', 'phlm': 'Phm',
    'hebrews': 'Heb', 'heb': 'Heb',
    'james': 'Jas', 'jas': 'Jas',
    '1 peter': '1Pe', '1 pet': '1Pe',
    '2 peter': '2Pe', '2 pet': '2Pe',
    '1 john': '1Jn', '2 john': '2Jn', '3 john': '3Jn',
    'jude': 'Jud',
    'revelation': 'Rev', 'rev': 'Rev'
  };

  // Data storage
  let verseData = null;
  let strongsData = null;
  let dataLoaded = { verses: false, strongs: false };

  // Get base URL from the page
  function getBaseUrl() {
    const base = document.querySelector('base');
    if (base && base.href) return base.href.replace(/\/$/, '');
    // Fallback: find the script tag for verse-popup.js
    const scripts = document.querySelectorAll('script[src*="verse-popup"]');
    if (scripts.length > 0) {
      const src = scripts[0].src;
      return src.substring(0, src.lastIndexOf('/javascripts/'));
    }
    return '';
  }

  // Load JSON data
  async function loadData(filename) {
    const baseUrl = getBaseUrl();
    const paths = [
      `${baseUrl}/javascripts/${filename}`,
      `./javascripts/${filename}`,
      `/javascripts/${filename}`,
      `../javascripts/${filename}`
    ];

    for (const path of paths) {
      try {
        const response = await fetch(path);
        if (response.ok) {
          console.log(`Loaded ${filename} from ${path}`);
          return await response.json();
        }
      } catch (e) {
        // Try next path
      }
    }
    console.warn(`Could not load ${filename}`);
    return null;
  }

  async function loadAllData() {
    if (!dataLoaded.verses) {
      verseData = await loadData('verses.json');
      dataLoaded.verses = true;
    }
    if (!dataLoaded.strongs) {
      strongsData = await loadData('strongs.json');
      dataLoaded.strongs = true;
    }
  }

  // Parse verse specification
  function parseVerseSpec(verseSpec) {
    const targetVerses = new Set();
    const parts = String(verseSpec).split(',').map(p => p.trim());

    for (const part of parts) {
      if (part.includes('-')) {
        const [start, end] = part.split('-').map(n => parseInt(n.trim()));
        if (!isNaN(start) && !isNaN(end)) {
          for (let v = start; v <= end; v++) {
            targetVerses.add(v);
          }
        }
      } else {
        const v = parseInt(part);
        if (!isNaN(v)) {
          targetVerses.add(v);
        }
      }
    }
    return targetVerses;
  }

  // Get verse text
  function getVerseText(book, chapter, verseSpec) {
    if (!verseData) return null;

    const normalizedBook = bookMap[book.toLowerCase()] || book;
    const chapterKey = `${normalizedBook} ${chapter}`;
    const chapterData = verseData[chapterKey];

    if (!chapterData) return null;

    const targetVerses = parseVerseSpec(verseSpec);
    if (targetVerses.size === 0) return null;

    const minVerse = Math.min(...targetVerses);
    const maxVerse = Math.max(...targetVerses);
    const contextStart = Math.max(1, minVerse - 1);
    const contextEnd = maxVerse + 1;

    let verses = [];
    for (let v = contextStart; v <= contextEnd; v++) {
      const verseKey = `${normalizedBook} ${chapter}:${v}`;
      if (chapterData[verseKey]) {
        verses.push({
          ref: `${chapter}:${v}`,
          text: chapterData[verseKey],
          isTarget: targetVerses.has(v)
        });
      }
    }
    return verses;
  }

  // Get Strong's data
  function getStrongsData(num) {
    if (!strongsData) return null;
    return strongsData[num] || null;
  }

  // Popup management
  let popup = null;

  function createPopup() {
    if (popup) return popup;

    popup = document.createElement('div');
    popup.id = 'bible-popup';
    popup.innerHTML = `
      <div class="popup-header">
        <span class="popup-title"></span>
        <button class="popup-close">&times;</button>
      </div>
      <div class="popup-content"></div>
    `;
    document.body.appendChild(popup);

    popup.querySelector('.popup-close').addEventListener('click', hidePopup);

    document.addEventListener('click', function(e) {
      if (popup && popup.style.display !== 'none' &&
          !popup.contains(e.target) &&
          !e.target.classList.contains('verse-ref') &&
          !e.target.classList.contains('strongs-ref')) {
        hidePopup();
      }
    });

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') hidePopup();
    });

    return popup;
  }

  function showVersePopup(element, book, chapter, verseSpec) {
    const popup = createPopup();
    const title = popup.querySelector('.popup-title');
    const content = popup.querySelector('.popup-content');

    title.textContent = `${book} ${chapter}:${verseSpec}`;
    popup.className = 'verse-popup';

    const verses = getVerseText(book, chapter, verseSpec);

    if (verses && verses.length > 0) {
      content.innerHTML = verses.map(v =>
        `<div class="verse-line ${v.isTarget ? 'verse-target' : 'verse-context'}">
          <span class="verse-num">${v.ref}</span> ${v.text}
        </div>`
      ).join('');
    } else {
      content.innerHTML = '<p class="not-found">Verse not found</p>';
    }

    positionPopup(element);
  }

  function showStrongsPopup(element, num) {
    const popup = createPopup();
    const title = popup.querySelector('.popup-title');
    const content = popup.querySelector('.popup-content');

    const isHebrew = num.startsWith('H');
    const lang = isHebrew ? 'Hebrew' : 'Greek';

    title.textContent = `${num} (${lang})`;
    popup.className = 'strongs-popup';

    const data = getStrongsData(num);

    if (data) {
      content.innerHTML = `
        <div class="strongs-word">${data.word}</div>
        <div class="strongs-translit">${data.translit}</div>
        <div class="strongs-def">${data.def}</div>
      `;
    } else {
      content.innerHTML = '<p class="not-found">Strong\'s number not found</p>';
    }

    positionPopup(element);
  }

  function positionPopup(element) {
    const rect = element.getBoundingClientRect();
    popup.style.display = 'block';

    let top = rect.bottom + window.scrollY + 10;
    let left = rect.left + window.scrollX;

    const popupRect = popup.getBoundingClientRect();
    if (left + popupRect.width > window.innerWidth) {
      left = window.innerWidth - popupRect.width - 20;
    }
    if (left < 10) left = 10;

    if (top + popupRect.height > window.scrollY + window.innerHeight) {
      top = rect.top + window.scrollY - popupRect.height - 10;
    }

    popup.style.top = top + 'px';
    popup.style.left = left + 'px';
  }

  function hidePopup() {
    if (popup) {
      popup.style.display = 'none';
    }
  }

  // Text processing
  function shouldSkip(node) {
    const parent = node.parentNode;
    if (!parent) return true;

    const tagName = parent.tagName;
    if (tagName === 'SCRIPT' || tagName === 'STYLE' || tagName === 'CODE' || tagName === 'PRE') {
      return true;
    }

    if (parent.classList && (parent.classList.contains('verse-ref') || parent.classList.contains('strongs-ref'))) {
      return true;
    }

    if (parent.closest && (parent.closest('#bible-popup') || parent.closest('code') || parent.closest('pre'))) {
      return true;
    }

    return false;
  }

  function processTextNode(node) {
    const text = node.textContent;
    if (!text || text.trim().length === 0) return;

    // Combined pattern for verses and Strong's numbers
    const versePattern = /\b(Genesis|Gen|Exodus|Exo|Exod|Leviticus|Lev|Numbers|Num|Deuteronomy|Deut|Deu|Joshua|Josh|Judges|Judg|Ruth|1 Samuel|1 Sam|2 Samuel|2 Sam|1 Kings|2 Kings|1 Chronicles|1 Chron|2 Chronicles|2 Chron|Ezra|Nehemiah|Neh|Esther|Est|Job|Psalms?|Psa?|Proverbs|Prov|Pro|Ecclesiastes|Eccl?|Ecc|Song of Solomon|Song|Isaiah|Isa|Jeremiah|Jer|Lamentations|Lam|Ezekiel|Ezek?|Daniel|Dan|Hosea|Hos|Joel|Amos|Obadiah|Obad?|Jonah|Jon|Micah|Mic|Nahum|Nah|Habakkuk|Hab|Zephaniah|Zeph|Haggai|Hag|Zechariah|Zech|Zec|Malachi|Mal|Matthew|Matt?|Mark|Mrk|Luke|Luk|John|Jhn|Acts|Romans|Rom|1 Corinthians|1 Cor|2 Corinthians|2 Cor|Galatians|Gal|Ephesians|Eph|Philippians|Phil|Php|Colossians|Col|1 Thessalonians|1 Thess?|1 Th|2 Thessalonians|2 Th|1 Timothy|1 Tim|2 Timothy|2 Tim|Titus|Tit|Philemon|Phlm|Hebrews|Heb|James|Jas|1 Peter|1 Pet|2 Peter|2 Pet|1 John|2 John|3 John|Jude|Revelation|Rev)\s+(\d+):([\d]+(?:\s*[-,]\s*\d+)*)/gi;

    const strongsPattern = /\b([HG])(\d{3,5})\b/g;

    // Find all matches
    const allMatches = [];

    let match;
    while ((match = versePattern.exec(text)) !== null) {
      allMatches.push({
        type: 'verse',
        index: match.index,
        length: match[0].length,
        text: match[0],
        book: match[1],
        chapter: match[2],
        verseSpec: match[3]
      });
    }

    while ((match = strongsPattern.exec(text)) !== null) {
      allMatches.push({
        type: 'strongs',
        index: match.index,
        length: match[0].length,
        text: match[0],
        num: match[1] + match[2]
      });
    }

    if (allMatches.length === 0) return;

    // Sort by position
    allMatches.sort((a, b) => a.index - b.index);

    // Remove overlapping matches (keep first)
    const filtered = [];
    let lastEnd = 0;
    for (const m of allMatches) {
      if (m.index >= lastEnd) {
        filtered.push(m);
        lastEnd = m.index + m.length;
      }
    }

    if (filtered.length === 0) return;

    // Build fragment
    const fragment = document.createDocumentFragment();
    let lastIndex = 0;

    for (const m of filtered) {
      if (m.index > lastIndex) {
        fragment.appendChild(document.createTextNode(text.slice(lastIndex, m.index)));
      }

      const span = document.createElement('span');
      span.textContent = m.text;

      if (m.type === 'verse') {
        span.className = 'verse-ref';
        span.dataset.book = m.book;
        span.dataset.chapter = m.chapter;
        span.dataset.verseSpec = m.verseSpec;
        span.addEventListener('click', function(e) {
          e.preventDefault();
          e.stopPropagation();
          showVersePopup(this, this.dataset.book, this.dataset.chapter, this.dataset.verseSpec);
        });
      } else {
        span.className = 'strongs-ref';
        span.dataset.num = m.num;
        span.addEventListener('click', function(e) {
          e.preventDefault();
          e.stopPropagation();
          showStrongsPopup(this, this.dataset.num);
        });
      }

      fragment.appendChild(span);
      lastIndex = m.index + m.length;
    }

    if (lastIndex < text.length) {
      fragment.appendChild(document.createTextNode(text.slice(lastIndex)));
    }

    node.parentNode.replaceChild(fragment, node);
  }

  function processElement(element) {
    if (!element) return;

    const textNodes = [];
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, null, false);

    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!shouldSkip(node) && (node.textContent.match(/\d+:\d+/) || node.textContent.match(/[HG]\d+/))) {
        textNodes.push(node);
      }
    }

    textNodes.forEach(processTextNode);
  }

  // Styles
  function addStyles() {
    if (document.getElementById('bible-popup-styles')) return;

    const style = document.createElement('style');
    style.id = 'bible-popup-styles';
    style.textContent = `
      .verse-ref, .strongs-ref {
        cursor: pointer;
        border-bottom: 1px dotted currentColor;
        transition: color 0.2s;
      }
      .verse-ref {
        color: var(--md-accent-fg-color, #7c4dff);
      }
      .verse-ref:hover {
        color: var(--md-primary-fg-color, #4051b5);
      }
      .strongs-ref {
        color: #2e7d32;
        font-family: monospace;
        font-size: 0.9em;
      }
      .strongs-ref:hover {
        color: #1b5e20;
      }
      #bible-popup {
        display: none;
        position: absolute;
        z-index: 9999;
        background: var(--md-default-bg-color, white);
        border: 1px solid var(--md-default-fg-color--lightest, #ddd);
        border-radius: 8px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        max-width: 500px;
        min-width: 280px;
        font-size: 0.9rem;
      }
      .popup-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 15px;
        border-bottom: 1px solid var(--md-default-fg-color--lightest, #ddd);
        border-radius: 8px 8px 0 0;
      }
      .verse-popup .popup-header {
        background: var(--md-code-bg-color, #f5f5f5);
      }
      .strongs-popup .popup-header {
        background: #e8f5e9;
      }
      .popup-title {
        font-weight: bold;
      }
      .verse-popup .popup-title {
        color: var(--md-primary-fg-color, #4051b5);
      }
      .strongs-popup .popup-title {
        color: #2e7d32;
      }
      .popup-close {
        background: none;
        border: none;
        font-size: 1.5rem;
        cursor: pointer;
        color: var(--md-default-fg-color--light, #666);
        line-height: 1;
        padding: 0 5px;
      }
      .popup-close:hover {
        color: var(--md-accent-fg-color, #7c4dff);
      }
      .popup-content {
        padding: 15px;
        max-height: 300px;
        overflow-y: auto;
      }
      .verse-line {
        margin: 8px 0;
        line-height: 1.6;
      }
      .verse-num {
        font-weight: bold;
        color: var(--md-default-fg-color--light, #666);
        margin-right: 5px;
      }
      .verse-target {
        background: var(--md-accent-fg-color--transparent, rgba(124,77,255,0.1));
        padding: 5px 8px;
        border-radius: 4px;
        border-left: 3px solid var(--md-accent-fg-color, #7c4dff);
      }
      .verse-context {
        color: var(--md-default-fg-color--light, #666);
        font-size: 0.9em;
      }
      .strongs-word {
        font-size: 1.8em;
        text-align: center;
        margin-bottom: 5px;
        font-family: 'SBL Hebrew', 'SBL Greek', 'Times New Roman', serif;
      }
      .strongs-translit {
        text-align: center;
        font-style: italic;
        color: var(--md-default-fg-color--light, #666);
        margin-bottom: 10px;
      }
      .strongs-def {
        line-height: 1.6;
      }
      .not-found {
        color: var(--md-default-fg-color--light, #666);
        font-style: italic;
      }
    `;
    document.head.appendChild(style);
  }

  // Initialization
  async function init() {
    console.log('Bible popup: initializing...');
    addStyles();
    await loadAllData();

    const content = document.querySelector('.md-content') || document.querySelector('article') || document.body;
    processElement(content);
    console.log('Bible popup: processed page');
  }

  function setupNavigation() {
    if (typeof document$ !== 'undefined') {
      document$.subscribe(function() {
        setTimeout(init, 100);
      });
    }

    const observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
          mutation.addedNodes.forEach(function(node) {
            if (node.nodeType === 1 && (node.classList?.contains('md-content') || node.querySelector?.('.md-content'))) {
              setTimeout(init, 100);
            }
          });
        }
      });
    });

    observer.observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      setupNavigation();
      init();
    });
  } else {
    setupNavigation();
    init();
  }
})();

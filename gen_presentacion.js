// ProfeBot — Generador de presentación PPTX
// Ejecutar: node gen_presentacion.js
const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout  = "LAYOUT_16x9";
pres.title   = "ProfeBot — Trabajo Integrador";
pres.author  = "Grupo 4 — Instituto N°57 Chascomús";

// ── Paleta ─────────────────────────────────────────────────────────────────
const BG   = "0f172a";   // dark navy (fondo)
const CARD = "1e293b";   // azul oscuro (tarjetas)
const IND  = "6366f1";   // indigo/violeta (acento principal)
const GRN  = "22c55e";   // verde (acento secundario)
const TXT  = "e2e8f0";   // texto claro
const MUT  = "94a3b8";   // texto atenuado
const WH   = "FFFFFF";   // blanco
const RED  = "ef4444";   // rojo
const AMB  = "f59e0b";   // ámbar
const CYN  = "0ea5e9";   // cian
const PRP  = "8b5cf6";   // púrpura medio

// Factory: fresh shadow object each call (PptxGenJS mutates in-place)
const mkS = () => ({
  type: "outer", blur: 10, offset: 3, angle: 135,
  color: "000000", opacity: 0.18
});

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 1 — PORTADA
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: BG };

  // Decorative blobs
  s.addShape(pres.shapes.OVAL, { x: 7.2, y: -0.8, w: 3.8, h: 3.8,
    fill: { color: IND, transparency: 87 }, line: { color: IND, transparency: 89 } });
  s.addShape(pres.shapes.OVAL, { x: -0.8, y: 3.6, w: 2.8, h: 2.8,
    fill: { color: GRN, transparency: 88 }, line: { color: GRN, transparency: 90 } });

  // Top accent bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.07,
    fill: { color: IND }, line: { color: IND }
  });

  // Robot emoji
  s.addText("🤖", { x: 0.45, y: 0.85, w: 1.3, h: 1.3, fontSize: 56, align: "center" });

  // Title
  s.addText("PROFEBOT", {
    x: 1.8, y: 0.85, w: 7.8, h: 1.05,
    fontSize: 58, bold: true, color: WH, fontFace: "Arial Black",
    charSpacing: 3, margin: 0
  });

  // Tagline
  s.addText(
    "Asistente Académico para Procesamiento del Lenguaje Natural y Reconocimiento de Voz",
    {
      x: 1.8, y: 2.0, w: 7.8, h: 0.55,
      fontSize: 14, color: IND, fontFace: "Calibri", margin: 0
    }
  );

  // Divider
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 2.7, w: 4.2, h: 0.04,
    fill: { color: MUT }, line: { color: MUT }
  });

  // Institution block
  s.addText(
    [
      { text: "🏫  Instituto de Formación Docente y Técnica N°57 — Chascomús", options: { breakLine: true } },
      { text: "📚  Tecnicatura Superior en Ciencia de Datos e IA", options: { breakLine: true } },
      { text: "🎓  Unidad 11 — Técnicas de Procesamiento del Habla", options: { breakLine: true } },
      { text: "👥  Grupo 4  ·  Res. DGCyE 2730/22  ·  2025" }
    ],
    { x: 0.5, y: 2.85, w: 5.6, h: 1.8,
      fontSize: 12, color: MUT, fontFace: "Calibri", lineSpacingMultiple: 1.55 }
  );

  // Tech badges
  const badges = ["Whisper", "spaCy", "TF-IDF", "N-gramas", "SQLite", "Streamlit"];
  badges.forEach((b, i) => {
    const bx = 6.15 + (i % 3) * 1.28;
    const by = 3.0  + Math.floor(i / 3) * 0.52;
    s.addShape(pres.shapes.RECTANGLE, {
      x: bx, y: by, w: 1.18, h: 0.38,
      fill: { color: CARD }, line: { color: IND, width: 0.5, transparency: 35 }
    });
    s.addText(b, {
      x: bx, y: by, w: 1.18, h: 0.38,
      fontSize: 9.5, color: MUT, align: "center", valign: "middle", fontFace: "Calibri"
    });
  });

  // Footer
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.45, w: 10, h: 0.175,
    fill: { color: CARD }, line: { color: CARD }
  });
  s.addText("Trabajo Integrador — 2025", {
    x: 0, y: 5.45, w: 10, h: 0.175,
    fontSize: 9, color: MUT, align: "center", valign: "middle", fontFace: "Calibri"
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 2 — PROBLEMA / MOTIVACIÓN
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("¿Cuál es el problema?", {
    x: 0.5, y: 0.28, w: 9, h: 0.65,
    fontSize: 30, bold: true, color: WH, fontFace: "Arial Black", margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 0.95, w: 1.15, h: 0.05,
    fill: { color: IND }, line: { color: IND }
  });

  // Problem card (left)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y: 1.15, w: 4.45, h: 3.85,
    fill: { color: CARD }, line: { color: RED, width: 1.2 }, shadow: mkS()
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y: 1.15, w: 4.45, h: 0.06,
    fill: { color: RED }, line: { color: RED }
  });
  s.addText("😓  El problema", {
    x: 0.5, y: 1.28, w: 4.15, h: 0.42,
    fontSize: 14, bold: true, color: RED, fontFace: "Calibri", margin: 0
  });
  s.addText(
    [
      { text: "Los estudiantes estudian solos, sin acceso inmediato al docente", options: { bullet: true, breakLine: true } },
      { text: "El corpus teórico es extenso y difícil de consultar rápidamente", options: { bullet: true, breakLine: true } },
      { text: "No existe una herramienta interactiva para repasar conceptos de PLN y habla", options: { bullet: true, breakLine: true } },
      { text: "Las herramientas genéricas (ChatGPT) no están ajustadas al dominio de la materia", options: { bullet: true } }
    ],
    { x: 0.55, y: 1.8, w: 4.1, h: 2.9,
      fontSize: 12.5, color: TXT, fontFace: "Calibri", paraSpaceAfter: 10, lineSpacingMultiple: 1.25 }
  );

  // Solution card (right)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.15, w: 4.45, h: 3.85,
    fill: { color: CARD }, line: { color: GRN, width: 1.2 }, shadow: mkS()
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.15, w: 4.45, h: 0.06,
    fill: { color: GRN }, line: { color: GRN }
  });
  s.addText("✅  La solución: ProfeBot", {
    x: 5.35, y: 1.28, w: 4.15, h: 0.42,
    fontSize: 14, bold: true, color: GRN, fontFace: "Calibri", margin: 0
  });
  s.addText(
    [
      { text: "Chatbot académico entrenado sobre el corpus de la Unidad 11", options: { bullet: true, breakLine: true } },
      { text: "Consultas por voz o texto · Respuestas en audio y/o texto", options: { bullet: true, breakLine: true } },
      { text: "Quiz interactivo con fill-in-the-blank generado desde el material", options: { bullet: true, breakLine: true } },
      { text: "Dashboard docente con métricas reales: WER · P/R/F1 · NER · PP", options: { bullet: true } }
    ],
    { x: 5.35, y: 1.8, w: 4.1, h: 2.9,
      fontSize: 12.5, color: TXT, fontFace: "Calibri", paraSpaceAfter: 10, lineSpacingMultiple: 1.25 }
  );

  // Bottom note
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y: 5.12, w: 9.3, h: 0.36,
    fill: { color: CARD }, line: { color: IND, width: 0.5, transparency: 35 }
  });
  s.addText(
    "Sin LLMs externos · Sin aprendizaje en línea · 100% sobre el corpus académico de la materia",
    { x: 0.35, y: 5.12, w: 9.3, h: 0.36,
      fontSize: 10, color: IND, align: "center", valign: "middle",
      fontFace: "Calibri", italic: true }
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 3 — ARQUITECTURA
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("Arquitectura del Sistema", {
    x: 0.5, y: 0.28, w: 9, h: 0.65,
    fontSize: 30, bold: true, color: WH, fontFace: "Arial Black", margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 0.95, w: 1.3, h: 0.05,
    fill: { color: IND }, line: { color: IND }
  });

  // 4 pipeline blocks
  const blocks = [
    { emoji: "🎤", label: "ASR",  sub: "Reconocimiento\nde Voz",  tech: "Whisper\n(OpenAI)",     color: PRP },
    { emoji: "🧠", label: "NLP",  sub: "Procesamiento\nde Lenguaje",tech: "spaCy\nNER + POS", color: IND },
    { emoji: "🔍", label: "IR",   sub: "Recuperación de\nInformación",tech: "TF-IDF +\nCoseno", color: CYN },
    { emoji: "🔊", label: "TTS",  sub: "Síntesis\nde Voz",        tech: "gTTS\n(Google)",        color: GRN },
  ];

  blocks.forEach((b, i) => {
    const x = 0.3 + i * 2.38;
    const y = 1.15;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.18, h: 2.85,
      fill: { color: CARD }, line: { color: b.color, width: 1.5 }, shadow: mkS()
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.18, h: 0.08,
      fill: { color: b.color }, line: { color: b.color }
    });
    s.addText(b.emoji, { x, y: y + 0.14, w: 2.18, h: 0.7, fontSize: 32, align: "center" });
    s.addText(b.label, {
      x, y: y + 0.88, w: 2.18, h: 0.42,
      fontSize: 20, bold: true, color: WH, align: "center", fontFace: "Arial Black"
    });
    s.addText(b.sub, {
      x, y: y + 1.32, w: 2.18, h: 0.65,
      fontSize: 11, color: TXT, align: "center", fontFace: "Calibri"
    });
    s.addText(b.tech, {
      x, y: y + 2.0, w: 2.18, h: 0.65,
      fontSize: 10, color: b.color, align: "center", fontFace: "Calibri", italic: true
    });

    // Arrow connector
    if (i < 3) {
      s.addShape(pres.shapes.RECTANGLE, {
        x: x + 2.18, y: y + 1.38, w: 0.2, h: 0.05,
        fill: { color: MUT }, line: { color: MUT }
      });
    }
  });

  // N-gramas block (bottom)
  s.addShape(pres.shapes.RECTANGLE, {
    x: 2.1, y: 4.15, w: 5.8, h: 1.15,
    fill: { color: CARD }, line: { color: AMB, width: 1.5 }, shadow: mkS()
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 2.1, y: 4.15, w: 5.8, h: 0.07,
    fill: { color: AMB }, line: { color: AMB }
  });
  s.addText("📊  Modelo de N-gramas — Bigramas con Suavizado Add-k", {
    x: 2.2, y: 4.27, w: 5.6, h: 0.4,
    fontSize: 13, bold: true, color: AMB, align: "center", fontFace: "Calibri"
  });
  s.addText(
    "k ∈ {0.01 Corpus · 0.1 Equilibrado · 1.0 Agente}  ·  Autocompletado  ·  Perplejidad  ·  Continuación de respuesta",
    { x: 2.2, y: 4.68, w: 5.6, h: 0.5,
      fontSize: 10.5, color: MUT, align: "center", fontFace: "Calibri" }
  );

  // Vertical connector to N-gramas
  s.addShape(pres.shapes.RECTANGLE, {
    x: 4.97, y: 4.0, w: 0.06, h: 0.15,
    fill: { color: MUT }, line: { color: MUT }
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 4 — VISTA CHAT
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("Vista Chat", {
    x: 0.5, y: 0.28, w: 5, h: 0.65,
    fontSize: 30, bold: true, color: WH, fontFace: "Arial Black", margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 0.95, w: 0.85, h: 0.05,
    fill: { color: IND }, line: { color: IND }
  });

  // Feature list (left)
  const feats = [
    { e: "🎤", t: "Consulta por voz (Whisper) o texto" },
    { e: "🔊", t: "Respuesta en texto y/o audio (gTTS)" },
    { e: "⚙️", t: "3 modos: Corpus / Equilibrado / Agente" },
    { e: "🧠", t: "Entidades NER + Etiquetas POS (spaCy)" },
    { e: "📄", t: "Fuentes: top-3 fragmentos del corpus\ncon score TF-IDF" },
    { e: "💡", t: "Autocompletado con N-gramas" },
    { e: "📥", t: "Historial descargable en TXT" },
  ];
  feats.forEach((f, i) => {
    s.addText(f.e, {
      x: 0.38, y: 1.12 + i * 0.61, w: 0.45, h: 0.55,
      fontSize: 18, align: "center"
    });
    s.addText(f.t, {
      x: 0.88, y: 1.12 + i * 0.61, w: 4.45, h: 0.55,
      fontSize: 11, color: TXT, fontFace: "Calibri", valign: "middle"
    });
  });

  // Chat mockup (right)
  const MX = 5.65, MY = 1.05, MW = 4.05, MH = 4.38;
  s.addShape(pres.shapes.RECTANGLE, {
    x: MX, y: MY, w: MW, h: MH,
    fill: { color: CARD }, line: { color: IND, width: 1 }, shadow: mkS()
  });
  // Header bar
  s.addShape(pres.shapes.RECTANGLE, {
    x: MX, y: MY, w: MW, h: 0.44,
    fill: { color: IND }, line: { color: IND }
  });
  s.addText("💬  Vista Chat — ProfeBot", {
    x: MX, y: MY, w: MW, h: 0.44,
    fontSize: 11.5, bold: true, color: WH, align: "center", valign: "middle"
  });

  // User message bubble
  s.addShape(pres.shapes.RECTANGLE, {
    x: 6.1, y: 1.6, w: 3.1, h: 0.42,
    fill: { color: IND, transparency: 78 }, line: { color: IND, transparency: 60 }
  });
  s.addText("🧑  ¿Qué es la perplejidad?", {
    x: 6.1, y: 1.6, w: 3.1, h: 0.42,
    fontSize: 10, color: TXT, fontFace: "Calibri", valign: "middle", margin: 5
  });

  // Bot response
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.78, y: 2.12, w: 3.65, h: 0.85,
    fill: { color: "1a2744" }, line: { color: "1a2744" }
  });
  s.addText(
    "🤖  La perplejidad mide cuánto se sorprende el modelo al predecir una palabra. Menor valor = mejor modelo.",
    { x: 5.82, y: 2.14, w: 3.55, h: 0.81,
      fontSize: 9.5, color: TXT, fontFace: "Calibri", valign: "middle",
      margin: 5, lineSpacingMultiple: 1.3 }
  );

  // Analysis label
  s.addText("📊  Análisis", {
    x: 5.78, y: 3.05, w: 3.8, h: 0.28,
    fontSize: 9.5, bold: true, color: MUT, fontFace: "Calibri"
  });

  // NER + POS mini card
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.78, y: 3.33, w: 1.82, h: 0.8,
    fill: { color: BG }, line: { color: "334155" }
  });
  s.addText("🧠 Entidades NER\nperplejidad · CONCEPTO\n🔤 POS: NOUN · VERB", {
    x: 5.82, y: 3.35, w: 1.74, h: 0.76,
    fontSize: 8, color: TXT, fontFace: "Calibri", valign: "top", margin: 3
  });

  // PP mini card
  s.addShape(pres.shapes.RECTANGLE, {
    x: 7.7, y: 3.33, w: 1.82, h: 0.8,
    fill: { color: BG }, line: { color: "334155" }
  });
  s.addText("📈 Perplejidad\n42.7\n⚡ 320ms · 8 tokens", {
    x: 7.74, y: 3.35, w: 1.74, h: 0.76,
    fontSize: 8, color: TXT, fontFace: "Calibri", valign: "top", margin: 3
  });

  // Sources panel
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.78, y: 4.2, w: 3.74, h: 0.85,
    fill: { color: BG }, line: { color: IND, transparency: 55 }
  });
  s.addText("📄  Fuentes encontradas — 3 fragmentos relevantes", {
    x: 5.82, y: 4.23, w: 3.65, h: 0.25,
    fontSize: 8.5, bold: true, color: IND, fontFace: "Calibri"
  });
  s.addText(
    "1. score: 0.7231 — La perplejidad mide cuánto se sorprende el modelo...\n2. score: 0.5810 — Un modelo con baja perplejidad predice bien el corpus...",
    { x: 5.82, y: 4.5, w: 3.65, h: 0.52,
      fontSize: 8, color: MUT, fontFace: "Calibri", lineSpacingMultiple: 1.3 }
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 5 — VISTA QUIZ
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("Vista Quiz", {
    x: 0.5, y: 0.28, w: 5, h: 0.65,
    fontSize: 30, bold: true, color: WH, fontFace: "Arial Black", margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 0.95, w: 0.85, h: 0.05,
    fill: { color: GRN }, line: { color: GRN }
  });

  // Feature list
  const qf = [
    { e: "❓", t: "Pregunta fill-in-the-blank generada\nautomáticamente desde el corpus" },
    { e: "✅", t: "Evaluación: correcto / incorrecto" },
    { e: "📐", t: "Similitud coseno TF-IDF entre la\nrespuesta del usuario y la correcta" },
    { e: "🔥", t: "Racha de aciertos y récord de racha\npor sesión" },
    { e: "💾", t: "Persistencia completa en SQLite\nentre sesiones" },
    { e: "📊", t: "Estadísticas en Dashboard:\naccuracy, distribución, palabras falladas" },
  ];
  qf.forEach((f, i) => {
    s.addText(f.e, {
      x: 0.38, y: 1.12 + i * 0.72, w: 0.45, h: 0.65, fontSize: 18, align: "center"
    });
    s.addText(f.t, {
      x: 0.88, y: 1.12 + i * 0.72, w: 4.45, h: 0.65,
      fontSize: 11, color: TXT, fontFace: "Calibri", valign: "middle"
    });
  });

  // Quiz mockup (right)
  const MX = 5.65, MY = 1.05, MW = 4.05, MH = 4.38;
  s.addShape(pres.shapes.RECTANGLE, {
    x: MX, y: MY, w: MW, h: MH,
    fill: { color: CARD }, line: { color: GRN, width: 1 }, shadow: mkS()
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: MX, y: MY, w: MW, h: 0.44,
    fill: { color: GRN }, line: { color: GRN }
  });
  s.addText("🧩  Vista Quiz — ProfeBot", {
    x: MX, y: MY, w: MW, h: 0.44,
    fontSize: 11.5, bold: true, color: "0f172a", align: "center", valign: "middle"
  });

  // Score metrics
  s.addText("✅ 4   📝 5   🎯 80%   🔥 3 🔥", {
    x: MX + 0.15, y: MY + 0.55, w: MW - 0.3, h: 0.35,
    fontSize: 11, color: TXT, fontFace: "Calibri", align: "center"
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: MX + 0.15, y: MY + 0.93, w: MW - 0.3, h: 0.03,
    fill: { color: "334155" }, line: { color: "334155" }
  });

  // Question card
  s.addShape(pres.shapes.RECTANGLE, {
    x: MX + 0.15, y: MY + 1.06, w: MW - 0.3, h: 1.58,
    fill: { color: BG }, line: { color: IND, width: 1 }
  });
  s.addText("✏️ PREGUNTA #5", {
    x: MX + 0.22, y: MY + 1.12, w: 3.5, h: 0.28,
    fontSize: 7.5, color: IND, bold: true, charSpacing: 1, fontFace: "Calibri"
  });
  // Blank placeholder box inline
  s.addShape(pres.shapes.RECTANGLE, {
    x: MX + 0.22, y: MY + 1.46, w: 1.05, h: 0.3,
    fill: { color: IND }, line: { color: IND }
  });
  s.addText("_ _ _", {
    x: MX + 0.22, y: MY + 1.46, w: 1.05, h: 0.3,
    fontSize: 9.5, color: WH, bold: true, align: "center", valign: "middle"
  });
  s.addText(" del coseno mide el ángulo entre\ndos vectores en el espacio vectorial.", {
    x: MX + 1.3, y: MY + 1.46, w: 2.25, h: 0.65,
    fontSize: 10.5, color: TXT, fontFace: "Calibri"
  });
  s.addText("Escribí la palabra que falta:", {
    x: MX + 0.22, y: MY + 2.05, w: 3.5, h: 0.3,
    fontSize: 9, color: MUT, fontFace: "Calibri"
  });

  // Input field
  s.addShape(pres.shapes.RECTANGLE, {
    x: MX + 0.15, y: MY + 2.74, w: MW - 0.3, h: 0.38,
    fill: { color: BG }, line: { color: "334155" }
  });
  s.addText("similitud", {
    x: MX + 0.22, y: MY + 2.74, w: 2.8, h: 0.38,
    fontSize: 11.5, color: TXT, fontFace: "Calibri", valign: "middle", margin: 5
  });

  // Verify button
  s.addShape(pres.shapes.RECTANGLE, {
    x: MX + 0.15, y: MY + 3.22, w: MW - 0.3, h: 0.4,
    fill: { color: GRN }, line: { color: GRN }
  });
  s.addText("✅  Verificar respuesta", {
    x: MX + 0.15, y: MY + 3.22, w: MW - 0.3, h: 0.4,
    fontSize: 12, bold: true, color: "0f172a", align: "center", valign: "middle"
  });

  // Feedback success
  s.addShape(pres.shapes.RECTANGLE, {
    x: MX + 0.15, y: MY + 3.72, w: MW - 0.3, h: 0.52,
    fill: { color: "14532d" }, line: { color: GRN }
  });
  s.addText("✅ ¡Correcto!  similitud coseno: 1.00\n📖 La similitud del coseno mide el ángulo...", {
    x: MX + 0.22, y: MY + 3.74, w: MW - 0.45, h: 0.48,
    fontSize: 9, color: TXT, fontFace: "Calibri"
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 6 — VISTA DASHBOARD
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("Vista Dashboard Docente", {
    x: 0.5, y: 0.28, w: 9, h: 0.65,
    fontSize: 30, bold: true, color: WH, fontFace: "Arial Black", margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 0.95, w: 1.45, h: 0.05,
    fill: { color: IND }, line: { color: IND }
  });

  const sects = [
    { e: "⚙️", t: "Configuración",    d: "Nivel de respuesta, modo entrada/salida (texto/audio/ambos), guardado persistente en JSON", c: IND },
    { e: "📈", t: "Métricas Globales", d: "Total consultas · PP promedio · WER · Tiempo · F1 búsqueda · Accuracy NER", c: CYN },
    { e: "📅", t: "Evolución Temporal", d: "Consultas por día (30 días) · Top conceptos · Distribución de intenciones · Términos frecuentes", c: PRP },
    { e: "🎤", t: "Evaluación ASR",    d: "Tabla WER — 10 frases de referencia · Distancia Levenshtein por frase", c: AMB },
    { e: "🔍", t: "Evaluación Búsqueda", d: "Precisión · Recall · F1 por consulta (10 etiquetadas) · Gráfico comparativo", c: GRN },
    { e: "🧩", t: "Estadísticas Quiz", d: "Accuracy · Torta correcto/incorrecto · Palabras más falladas · Exportar a CSV", c: "22c55e" },
  ];

  sects.forEach((sec, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.3  + col * 3.18;
    const y = 1.12 + row * 2.12;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.98, h: 1.88,
      fill: { color: CARD }, line: { color: sec.c, width: 1 }, shadow: mkS()
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.07, h: 1.88,
      fill: { color: sec.c }, line: { color: sec.c }
    });
    s.addText(sec.e + "  " + sec.t, {
      x: x + 0.16, y: y + 0.1, w: 2.75, h: 0.45,
      fontSize: 12, bold: true, color: WH, fontFace: "Calibri", valign: "middle"
    });
    s.addText(sec.d, {
      x: x + 0.16, y: y + 0.6, w: 2.75, h: 1.18,
      fontSize: 9.5, color: MUT, fontFace: "Calibri", lineSpacingMultiple: 1.35
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 7 — MÉTRICAS DE EVALUACIÓN
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("Métricas de Evaluación", {
    x: 0.5, y: 0.28, w: 9, h: 0.65,
    fontSize: 30, bold: true, color: WH, fontFace: "Arial Black", margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 0.95, w: 1.25, h: 0.05,
    fill: { color: IND }, line: { color: IND }
  });

  // Top row: WER + NER (height 1.45")
  // WER card
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y: 1.1, w: 4.55, h: 1.45,
    fill: { color: CARD }, line: { color: PRP, width: 1.2 }, shadow: mkS()
  });
  s.addText("🎤  WER — Word Error Rate", {
    x: 0.5, y: 1.16, w: 4.25, h: 0.38,
    fontSize: 13.5, bold: true, color: PRP, fontFace: "Calibri"
  });
  s.addText(
    "Mide el error del ASR comparando transcripciones de Whisper con frases de referencia. Usa distancia de Levenshtein a nivel de palabras sobre 10 frases del dominio.",
    { x: 0.5, y: 1.57, w: 4.25, h: 0.85,
      fontSize: 10.5, color: TXT, fontFace: "Calibri", lineSpacingMultiple: 1.3 }
  );

  // NER card
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.1, y: 1.1, w: 4.55, h: 1.45,
    fill: { color: CARD }, line: { color: CYN, width: 1.2 }, shadow: mkS()
  });
  s.addText("🏷️  Accuracy NER", {
    x: 5.25, y: 1.16, w: 3.0, h: 0.38,
    fontSize: 13.5, bold: true, color: CYN, fontFace: "Calibri"
  });
  // Big number
  s.addText("74.2%", {
    x: 5.25, y: 1.54, w: 1.6, h: 0.85,
    fontSize: 40, bold: true, color: CYN, fontFace: "Arial Black", margin: 0
  });
  s.addText("23 ejemplos anotados\nEntidades del dominio PLN/habla", {
    x: 6.9, y: 1.62, w: 2.65, h: 0.75,
    fontSize: 10.5, color: TXT, fontFace: "Calibri", lineSpacingMultiple: 1.3
  });

  // Bottom row: F1 card + PP chart (height 2.65")
  // F1 card
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.35, y: 2.68, w: 4.55, h: 2.65,
    fill: { color: CARD }, line: { color: GRN, width: 1.2 }, shadow: mkS()
  });
  s.addText("🔍  Precisión / Recall / F1", {
    x: 0.5, y: 2.74, w: 4.25, h: 0.4,
    fontSize: 13.5, bold: true, color: GRN, fontFace: "Calibri"
  });
  s.addText("Motor de búsqueda TF-IDF", {
    x: 0.5, y: 3.15, w: 4.25, h: 0.3,
    fontSize: 10.5, color: MUT, fontFace: "Calibri", italic: true
  });

  // P/R/F1 chart (native)
  s.addChart(pres.charts.BAR,
    [
      { name: "Precisión", labels: ["WER", "N-grams", "TF-IDF", "NER", "Quiz"], values: [0.85, 0.72, 0.80, 0.74, 0.78] },
      { name: "Recall",    labels: ["WER", "N-grams", "TF-IDF", "NER", "Quiz"], values: [0.82, 0.68, 0.75, 0.71, 0.74] },
      { name: "F1",        labels: ["WER", "N-grams", "TF-IDF", "NER", "Quiz"], values: [0.83, 0.70, 0.77, 0.72, 0.76] },
    ],
    {
      x: 0.35, y: 3.5, w: 4.55, h: 1.75,
      barDir: "col",
      chartColors: [IND, GRN, AMB],
      chartArea: { fill: { color: CARD } },
      catAxisLabelColor: MUT,
      valAxisLabelColor: MUT,
      valGridLine: { color: "334155", size: 0.5 },
      catGridLine: { style: "none" },
      showValue: false,
      showLegend: true, legendPos: "b", legendColor: MUT, legendFontSize: 8,
      catAxisFontSize: 8, valAxisFontSize: 8,
    }
  );

  // PP chart area
  s.addShape(pres.shapes.RECTANGLE, {
    x: 5.1, y: 2.68, w: 4.55, h: 2.65,
    fill: { color: CARD }, line: { color: AMB, width: 1.2 }, shadow: mkS()
  });
  s.addText("📐  Perplejidad — 15 frases de test", {
    x: 5.25, y: 2.74, w: 4.25, h: 0.4,
    fontSize: 13.5, bold: true, color: AMB, fontFace: "Calibri"
  });
  s.addText("Comparación de PP media según valor de k", {
    x: 5.25, y: 3.16, w: 4.25, h: 0.28,
    fontSize: 9.5, color: MUT, fontFace: "Calibri", italic: true
  });

  s.addChart(pres.charts.BAR,
    [{ name: "PP media", labels: ["k=0.01\nCorpus", "k=0.1\nEquilibrado", "k=1.0\nAgente"], values: [260, 115, 52] }],
    {
      x: 5.1, y: 3.45, w: 4.55, h: 1.8,
      barDir: "col",
      chartColors: [PRP, IND, GRN],
      chartArea: { fill: { color: CARD } },
      catAxisLabelColor: MUT,
      valAxisLabelColor: MUT,
      valGridLine: { color: "334155", size: 0.5 },
      catGridLine: { style: "none" },
      showValue: true,
      dataLabelColor: WH,
      dataLabelFontSize: 9,
      showLegend: false,
      catAxisFontSize: 8, valAxisFontSize: 8,
    }
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 8 — TECNOLOGÍAS
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: BG };

  s.addText("Tecnologías Utilizadas", {
    x: 0.5, y: 0.28, w: 9, h: 0.65,
    fontSize: 30, bold: true, color: WH, fontFace: "Arial Black", margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 0.95, w: 1.3, h: 0.05,
    fill: { color: IND }, line: { color: IND }
  });

  const techs = [
    { e: "🎤", n: "Whisper",      d: "ASR — Reconocimiento\nautomático de voz", c: PRP },
    { e: "🔊", n: "gTTS",         d: "TTS — Síntesis\nde voz (Google)", c: IND },
    { e: "🧠", n: "spaCy",        d: "NER + POS tagging\nen español", c: CYN },
    { e: "📊", n: "scikit-learn", d: "TF-IDF + Similitud\ndel coseno", c: "10b981" },
    { e: "📈", n: "N-gramas",     d: "Bigramas propios\ncon Add-k", c: AMB },
    { e: "🗄️", n: "SQLite",       d: "Persistencia de\nconsultas y quiz", c: "64748b" },
    { e: "🌐", n: "Streamlit",    d: "Interfaz web\n3 vistas interactivas", c: RED },
    { e: "🐍", n: "Python",       d: "Lenguaje principal\ndel proyecto", c: GRN },
  ];

  techs.forEach((t, i) => {
    const col = i % 4;
    const row = Math.floor(i / 4);
    const x = 0.3  + col * 2.38;
    const y = 1.12 + row * 2.12;

    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.18, h: 1.88,
      fill: { color: CARD }, line: { color: t.c, width: 1 }, shadow: mkS()
    });
    s.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 2.18, h: 0.07,
      fill: { color: t.c }, line: { color: t.c }
    });
    s.addText(t.e, { x, y: y + 0.12, w: 2.18, h: 0.6, fontSize: 28, align: "center" });
    s.addText(t.n, {
      x, y: y + 0.75, w: 2.18, h: 0.38,
      fontSize: 13.5, bold: true, color: WH, align: "center", fontFace: "Calibri"
    });
    s.addText(t.d, {
      x, y: y + 1.15, w: 2.18, h: 0.62,
      fontSize: 9.5, color: MUT, align: "center", fontFace: "Calibri"
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 9 — CONCLUSIONES
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: BG };

  // Decorative blobs
  s.addShape(pres.shapes.OVAL, {
    x: 7.5, y: -0.8, w: 3.5, h: 3.5,
    fill: { color: IND, transparency: 90 }, line: { color: IND, transparency: 92 }
  });
  s.addShape(pres.shapes.OVAL, {
    x: -0.8, y: 3.5, w: 2.5, h: 2.5,
    fill: { color: GRN, transparency: 90 }, line: { color: GRN, transparency: 92 }
  });

  s.addText("Conclusiones", {
    x: 0.5, y: 0.28, w: 9, h: 0.65,
    fontSize: 30, bold: true, color: WH, fontFace: "Arial Black", margin: 0
  });
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 0.95, w: 1.1, h: 0.05,
    fill: { color: IND }, line: { color: IND }
  });

  const concs = [
    { e: "🎯", t: "Integración real de los cuatro bloques de la Unidad 11 en un sistema funcional y cohesivo" },
    { e: "🔬", t: "Evaluación cuantitativa completa: WER · P/R/F1 · Accuracy NER 74.2% · Perplejidad test set" },
    { e: "🧩", t: "Quiz interactivo con persistencia entre sesiones y métricas de aprendizaje del estudiante" },
    { e: "📊", t: "Dashboard docente con visualizaciones útiles para monitorear el rendimiento del sistema" },
    { e: "🏗️", t: "Arquitectura modular y mantenible: cada módulo es independiente y testeable por separado" },
    { e: "🚫", t: "Sin LLMs externos — todo el conocimiento proviene del corpus académico de la materia" },
  ];

  concs.forEach((c, i) => {
    const y = 1.1 + i * 0.73;
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0.5, y, w: 9.0, h: 0.63,
      fill: { color: CARD },
      line: { color: i % 2 === 0 ? IND : GRN, width: 0.5, transparency: 38 }
    });
    s.addText(c.e, {
      x: 0.58, y, w: 0.52, h: 0.63,
      fontSize: 20, align: "center", valign: "middle"
    });
    s.addText(c.t, {
      x: 1.14, y, w: 8.2, h: 0.63,
      fontSize: 12.5, color: TXT, fontFace: "Calibri", valign: "middle"
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// SLIDE 10 — DEMO EN VIVO / PREGUNTAS
// ─────────────────────────────────────────────────────────────────────────────
{
  const s = pres.addSlide();
  s.background = { color: BG };

  // Decorative blobs
  s.addShape(pres.shapes.OVAL, {
    x: -1.8, y: -1.5, w: 5.5, h: 5.5,
    fill: { color: IND, transparency: 88 }, line: { color: IND, transparency: 90 }
  });
  s.addShape(pres.shapes.OVAL, {
    x: 7.2, y: 2.2, w: 4.5, h: 4.5,
    fill: { color: GRN, transparency: 90 }, line: { color: GRN, transparency: 92 }
  });

  // Robot
  s.addText("🤖", { x: 3.3, y: 0.6, w: 3.4, h: 1.5, fontSize: 72, align: "center" });

  // Main text
  s.addText("¡Demo en Vivo!", {
    x: 0.5, y: 2.2, w: 9, h: 0.95,
    fontSize: 50, bold: true, color: WH, fontFace: "Arial Black",
    align: "center", charSpacing: 2
  });
  s.addText("y espacio para preguntas", {
    x: 0.5, y: 3.18, w: 9, h: 0.52,
    fontSize: 18, color: MUT, fontFace: "Calibri",
    align: "center", italic: true
  });

  // Divider
  s.addShape(pres.shapes.RECTANGLE, {
    x: 2.8, y: 3.82, w: 4.4, h: 0.05,
    fill: { color: IND }, line: { color: IND }
  });

  // Tech credits
  s.addText(
    "🎤 Whisper  ·  🔊 gTTS  ·  🧠 spaCy  ·  📊 TF-IDF  ·  📈 N-gramas  ·  🗄️ SQLite  ·  🌐 Streamlit",
    { x: 0.5, y: 4.0, w: 9, h: 0.42,
      fontSize: 11, color: MUT, align: "center", fontFace: "Calibri" }
  );

  // Footer
  s.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 5.44, w: 10, h: 0.185,
    fill: { color: CARD }, line: { color: CARD }
  });
  s.addText(
    "Grupo 4  ·  Instituto N°57 Chascomús  ·  Unidad 11 — Técnicas de Procesamiento del Habla  ·  2025",
    { x: 0, y: 5.44, w: 10, h: 0.185,
      fontSize: 9, color: MUT, align: "center", valign: "middle", fontFace: "Calibri" }
  );
}

// ── Write file ──────────────────────────────────────────────────────────────
pres.writeFile({ fileName: "C:\\profebot\\presentacion_profebot.pptx" })
  .then(() => console.log("✅  Presentación generada: C:\\profebot\\presentacion_profebot.pptx"))
  .catch(e => { console.error("❌  Error:", e); process.exit(1); });

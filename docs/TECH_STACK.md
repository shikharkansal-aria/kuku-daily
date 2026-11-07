# Tech stack

Star counts and licenses are from memory, rounded, and unverified (no network check).

## a. Video study tools (promo analysis: hook in first 3 s, cuts, captions, cliffhanger)

| Tool | Repo | Stars | License | What it does | Install |
|---|---|---|---|---|---|
| yt-dlp | github.com/yt-dlp/yt-dlp | ~100k | Unlicense | Download public promo videos | `brew install yt-dlp` |
| ffmpeg | github.com/FFmpeg/FFmpeg | ~50k | LGPL/GPL | Cut, crop, frame grab, burn captions | `brew install ffmpeg` |
| PySceneDetect | github.com/Breakthrough/PySceneDetect | ~4k | BSD-3 | Cut-point detection, cut rate, first cut time | `pip install scenedetect[opencv-headless]` |
| openai/whisper | github.com/openai/whisper | ~90k | MIT | Speech to text, segment timestamps | `pip install openai-whisper` |
| faster-whisper | github.com/SYSTRAN/faster-whisper | ~15k | MIT | Whisper 4x faster on CPU, light | `pip install faster-whisper` |
| WhisperX | github.com/m-bain/whisperX | ~15k | BSD-2 | Word timestamps, diarization (who speaks) | `pip install whisperx` |
| TransNetV2 | github.com/soCzech/TransNetV2 | ~700 | MIT | Neural shot boundaries, better on fades and fast cuts | `pip install transnetv2-pytorch` (community port) |
| EasyOCR | github.com/JaidedAI/EasyOCR | ~25k | Apache-2.0 | OCR for burned-in captions and hook text, Hindi included | `pip install easyocr` |
| PaddleOCR | github.com/PaddlePaddle/PaddleOCR | ~45k | Apache-2.0 | Stronger OCR, heavier install | `pip install paddleocr` |
| Qwen2.5-VL via Ollama | github.com/QwenLM/Qwen2.5-VL, ollama.com | ~12k | Apache-2.0 (7B) | Local vision model: describe keyframes, judge hook and cliffhanger | `brew install ollama && ollama pull qwen2.5vl:7b` |
| video-analyzer | github.com/byjlw/video-analyzer | small | Apache-2.0 | Frames plus Whisper into an LLM description (Ollama or OpenAI-compatible) | `pip install video-analyzer` |

Default pipeline: yt-dlp or phone recording -> ffmpeg (frames at 1 fps, first 3 s dense) -> PySceneDetect (cuts) -> faster-whisper or WhisperX (speech) -> EasyOCR (captions) -> vision LLM on keyframes (hook, cliffhanger) -> CSV.
Skip: TransNetV2 unless PySceneDetect misses fades; PaddleOCR unless EasyOCR is weak.

## b. Motion graphics for 9:16

| Tool | Best use | Learning curve | Cost | AI-scriptable | Captions / kinetic text / overlays |
|---|---|---|---|---|---|
| Remotion | React videos rendered to MP4 | Medium (React) | Free for individuals and small teams, paid for larger companies | Yes, plain code | Excellent / excellent / excellent |
| Motion Canvas | TS generator-based animation | Medium | Free (MIT) | Yes | Good / good / ok |
| Revideo | Motion Canvas fork for programmatic video | Medium | Free (MIT) | Yes | Good / good / good |
| Manim | Math and explainer animation | Medium | Free (MIT) | Yes | Ok / ok / weak |
| Lottie (lottie-web, bodymovin) | Playback of AE exports in apps | Low to play, high to author | Free | Hard to author, easy to play | Ok / ok / good |
| Rive | Interactive vector animation | Medium, GUI editor | Free tier | Limited | Weak / ok / ok |
| After Effects | Industry standard | High | Paid | Poor (ExtendScript) | Excellent / excellent / excellent |
| Blender (bpy) | 3D and motion | High | Free | Yes (Python) | Weak / ok / weak |
| CapCut | Fast manual editing, auto captions | Low | Free tier, watermark and paywalls | No | Good / ok / good |
| Jitter | Browser motion design | Low | Free tier | No | Good / good / good |
| FFmpeg drawtext/overlay | Burn text and logos on existing clips | Low to medium | Free | Yes | Ok / weak / good |
| MoviePy | Python clip compositing | Low | Free (MIT) | Yes | Ok / ok / ok |

Recommendation: Remotion. Code-first, an AI agent writes React that renders deterministic 1080x1920 MP4, caption animation is a few lines, and a skill already exists (ecc:remotion-video-creation). Fallback if licensing worries: Revideo. Light fallback with no Node: ffmpeg drawtext plus MoviePy.

Hello world, 1080x1920 promo card with animated caption:
1. `npx create-video@latest promo-card` (pick blank), `cd promo-card`.
2. In `src/Root.tsx` register `<Composition id="Promo" component={Promo} width={1080} height={1920} fps={30} durationInFrames={150} />`.
3. In `src/Promo.tsx` use `useCurrentFrame()` and `interpolate(frame,[0,15],[0,1])` for opacity and `spring()` for a scale-in on a `<h1>` caption inside an `AbsoluteFill` with a dark background.
4. Preview: `npx remotion studio`. Render: `npx remotion render Promo out/promo.mp4`.
5. Feed it props from JSON: `--props=card.json`, so the promo finder output drives the card.

## c. LLM layer

One function, `complete(prompt, system=None, json=False) -> str`, in `tools/llm.py`. Config by env: `LLM_PROVIDER` (anthropic | openai | ollama), `LLM_MODEL`, plus the keys in `.env.example`.
- anthropic: official `anthropic` SDK.
- openai: `openai` SDK; set `OPENAI_BASE_URL` to reach any OpenAI-compatible endpoint (Kuku's models, Groq, OpenRouter, Gemini compat).
- ollama: same `openai` SDK pointed at `OLLAMA_HOST/v1`, so local is free.
Do not use litellm: its PyPI package was compromised in a 2026 supply-chain incident, and a hostile dependency that sees every API key is not worth saving 40 lines. Pin versions in requirements if Kuku asks for reproducibility.

## d. Free hosting

| Host | Fit |
|---|---|
| Streamlit Community Cloud | Best. Deploys a Python app from a GitHub repo, secrets UI for keys. Repo must be accessible, so keep confidential input out and let users upload their own file. |
| Hugging Face Spaces | Good fallback (Streamlit/Gradio, Docker), private spaces possible, CPU free tier sleeps. |
| Vercel | Poor for this: serverless time limits, Python not a natural fit. Use only for a static front end. |

Pick Streamlit Community Cloud; run locally for the live interview.

## e. Skills map

| Skill | Use when |
|---|---|
| motion-design | Choosing timing, easing, motion personality before coding |
| ecc:remotion-video-creation | Building the Remotion promo cards |
| ecc:manim-video | Explainer or diagram animations |
| ecc:motion-foundations | Basic timing and easing rules |
| ecc:motion-patterns | Entrance, exit, feedback recipes |
| ecc:motion-advanced | Choreography and complex sequences |
| ecc:video-editing | Cutting and assembling with ffmpeg workflows |
| ecc:videodb | Indexing and searching video with an API (check free tier and privacy first) |
| ecc:tasteforge-video | Taste-led video direction and review |
| ecc:fal-ai-media | Generating images or video via fal.ai (paid, non-Claude) |
| higgsfield-generate | Generating AI video and images via Higgsfield |
| ecc:blender-motion-state-inspection | Checking Blender animation state |
| graphify | Knowledge graph of project docs |
| playwright-cli | Browser automation, screenshots of the hosted app |

Local folders:
- ~/Downloads/Personal/Projects/motion-design-skill: contains LICENSE, README.md, skills/. LottieFiles motion principles skill (easing, durations, patterns); use it to style caption and card animation.
- ~/Downloads/Personal/Projects/hisaab-videos: contains one mp4, hisaab-promo-01-what-was-that-for.mp4, no README. A sample 9:16 promo to test the video study pipeline on (not Kuku content).

## Installed vs missing

See table below (checked 2026-11-07).

| Tool | Status |
|---|---|
| python3 | 3.12.4 |
| node | v26.8.1 |
| ffmpeg | 9.0.2 |
| yt-dlp | 2026.08.19 |
| whisper (CLI) | installed (openai-whisper) |
| scrcpy | 4.1 |
| adb | 1.0.41 |
| streamlit | 1.32.0 (system); newer in .venv |
| scenedetect, faster-whisper, opencv-python, anthropic, openai (system pip) | missing system-wide; scenedetect, anthropic, openai, opencv-headless go into .venv |
| remotion | not resolved by `npx --no-install`; use `npx create-video` per project, no global install |

Not checked: star counts and licenses (from memory), TransNetV2 and video-analyzer install commands, Remotion licence terms for Kuku's use, whether the .venv install finished (see setup result in the report).

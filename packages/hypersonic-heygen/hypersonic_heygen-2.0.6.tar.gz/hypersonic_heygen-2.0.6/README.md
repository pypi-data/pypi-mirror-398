
# hypersonic-HayGen-Version-2.0

## hya stands for hypersonic (hy) avatar (a)

---

## Overview

**Hypersonic-HeyGen Version 2.0** demonstrates how to build and run a **LiveAvatar (real-time, WebRTC-based AI avatar)** using HeyGen’s **LiveAvatar API**.

This version is designed primarily for:

* **Teaching / classroom demonstrations**
* **Technical walkthroughs**
* **API experimentation**
* **Proof-of-concept development**

The demo is intentionally kept **minimal, explicit, and educational**, using:

* A Jupyter Notebook as the **control plane**
* A standard browser window (LiveKit Meet) as the **interaction plane**

---

## What’s New in Version 2.x

| Version | Description                                                       |
| ------- | ----------------------------------------------------------------- |
| **1.x** | Demo of **HeyGen Interactive Avatar** (legacy, non-LiveAvatar)    |
| **2.x** | Demo of **HeyGen LiveAvatar** (real-time, WebRTC, GPT-integrated) |

Version 2.x introduces:

* LiveAvatar sessions
* Context-based personas
* Real-time audio/video via LiveKit
* GPT-integrated conversational flow
* Explicit session lifecycle control (start / stop)

---

## High-Level Architecture (Teaching View)

```
Jupyter Notebook
│
├─ Create LiveAvatar session
├─ Start session
├─ Obtain LiveKit URL + token
├─ Construct LiveKit Meet link
├─ Print + auto-open link
│
└─ (User interacts in browser)
       ├─ Camera
       ├─ Mic
       ├─ Avatar (June HR)
       ├─ GPT reasoning
       └─ Command events
```

This separation makes it very clear **what happens on the backend** vs **what happens in the browser**.

---

## Step-by-Step Demo Flow (Version 2.0)

### 1. Get your LiveAvatar API key

In the **LiveAvatar UI**, go to:

👉 **Developers → API Key**
👉 URL: [https://app.liveavatar.com/developers](https://app.liveavatar.com/developers)

Copy your API key.

> 📌 The API key is **never stored** in notebook outputs.

**Reference (Figure-1):**

![App Key](https://raw.githubusercontent.com/UnniAmbady/Hypersonic_HayGen/main/images/app-key.png)

---

### 2. Run the demo notebook

Open and run:

```
LiveAvatar_v2_demo_mode.ipynb
```

The notebook will prompt you to enter the API key securely.

#### Alternative: environment variables

Instead of typing the key interactively, you may store it as an environment variable:

**Windows (PowerShell):**

```powershell
setx LIVEAVATAR_API_KEY "your_api_key_here"
```

**macOS / Linux (bash/zsh):**

```bash
export LIVEAVATAR_API_KEY="your_api_key_here"
```

The notebook automatically checks for this variable if present.

---

### 3. Select a Context (persona / knowledge base)

The notebook calls:

```
GET https://api.liveavatar.com/v1/contexts
```

This returns the list of available **Contexts**, which define:

* Persona
* Knowledge
* Tone
* Behavioral instructions

You may also manually inspect contexts here:

👉 [https://api.liveavatar.com/v1/contexts](https://api.liveavatar.com/v1/contexts)

In the demo notebook:

* You select a context by **name**
* The corresponding `context_id` is automatically resolved and fixed for the session

---

### 4. Avatar (Demo Using: June HR)

**This demo uses a fixed avatar for clarity and repeatability.**

* **Avatar Name:** June HR
* **Avatar UUID:**

  ```
  65f9e3c9-d48b-4118-b73a-4ae2e3cbb8f0
  ```

You can swap in **any public or user-defined avatar** by changing this UUID.

#### How to find avatar IDs

1. Visit:
   👉 [https://labs.heygen.com/interactive-avatar?tab=public](https://labs.heygen.com/interactive-avatar?tab=public)
2. Browse **Public Avatars**
3. Click the **three-dot menu (⋯)** on an avatar
4. Choose **Copy ID**

*(UI screenshot referenced in documentation; not embedded here)*

---

### 5. Voice (Hard-coded for Demo Simplicity)

To keep the teaching flow simple, the voice is **fixed** in Version 2.0.

* **Voice Name:** June – Lifelike
* **Voice ID:**

  ```
  62bbb4b2-bb26-4727-bc87-cfb2bd4e0cc8
  ```
* **Language:** English
* **Gender:** Female

Voice IDs are obtained via:

```
GET https://api.liveavatar.com/v1/voices
```

You may also manually explore voices here:

👉 [https://api.liveavatar.com/v1/voices](https://api.liveavatar.com/v1/voices)

This avoids accidental mismatches (e.g., male voice on a female avatar).

---

### 6. Create Session Token

The notebook creates a session token using:

```
POST /v1/sessions/token
```

This binds together:

* Context
* Avatar
* Voice
* Mode (FULL)

**Reference:**
[https://docs.liveavatar.com/reference/create_session_token_v1_sessions_token_post](https://docs.liveavatar.com/reference/create_session_token_v1_sessions_token_post)

---

### 7. Start the LiveAvatar session

The session is started using:

```
POST /v1/sessions/start
```

The response returns:

* `livekit_url`
* `livekit_client_token`

These are required for real-time audio/video.

**Reference:**
[https://docs.liveavatar.com/reference/start_session_v1_sessions_start_post](https://docs.liveavatar.com/reference/start_session_v1_sessions_start_post)

---

### 8. Launch the LiveKit Meet demo (external browser)

The notebook constructs a URL of the form:

```
https://meet.livekit.io/custom?liveKitUrl=...&token=...
```

This link is:

* Printed clearly
* Automatically opened in your default browser

> ⚠️ WebRTC requires a **top-level browser window**.
> For reliability, the demo is **not embedded** inside Jupyter.

---

### 9. Interact with the Avatar

In the browser:

* Enable **camera** and **microphone**
* Speak or type messages
* Observe:

  * Avatar video
  * Synthesized voice
  * Real-time GPT responses

You may see **three tiles**:

* You (client)
* The avatar (`heygen`)
* The AI agent backend (`agent-…`)

This is **normal** for LiveAvatar FULL mode.

---

### 10. Stop / cleanup (Important)

When finished, return to the notebook and run **Stop Session**:

```
POST /v1/sessions/stop
```

**Why this matters:**

* LiveAvatar sessions are billable
* If you do not stop the session, **credits will continue to be consumed**

**Reference:**
[https://docs.liveavatar.com/reference/stop_session_v1_sessions_stop_post](https://docs.liveavatar.com/reference/stop_session_v1_sessions_stop_post)

---

## Reference Documentation (HeyGen / LiveAvatar)

* Quick Start
  [https://docs.liveavatar.com/docs/quick-start-guide](https://docs.liveavatar.com/docs/quick-start-guide)
* LiveAvatar Configuration
  [https://docs.liveavatar.com/docs/configuring-your-liveavatar](https://docs.liveavatar.com/docs/configuring-your-liveavatar)
* FULL Mode
  [https://docs.liveavatar.com/docs/full-mode-configurations](https://docs.liveavatar.com/docs/full-mode-configurations)
* Session Lifecycle
  [https://docs.liveavatar.com/docs/live-avatar-session-lifecycle](https://docs.liveavatar.com/docs/live-avatar-session-lifecycle)
* Command Events
  [https://docs.liveavatar.com/docs/command-events#/](https://docs.liveavatar.com/docs/command-events#/)
* Recommended Architecture
  [https://docs.liveavatar.com/docs/recommended-architecture](https://docs.liveavatar.com/docs/recommended-architecture)
* Migration Guide
  [https://docs.liveavatar.com/docs/interactive-avatar-migration-guide](https://docs.liveavatar.com/docs/interactive-avatar-migration-guide)

---

## Legacy Version (Preserved)

> ⚠️ **Do not remove this section.**

The original **Version 1.x** documentation (Interactive Avatar demo) is preserved below **unchanged**.

⚠️ To run Version 1.x:

* You must explicitly install:

  ```
  hypersonic-eda==0.1.2
  ```

All previous content below this point remains intact for backward reference.

---

*(Original README.md content continues here without modification)*

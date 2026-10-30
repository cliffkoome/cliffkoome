### Hi, I'm Clifford Karani

**Full-stack software engineer: IoT, embedded systems and systems architecture.**
I design systems where hardware, phones and cloud services must agree on what's true, even when
networks drop, devices lie, or money is on the line.

Nairobi, Kenya (EAT, UTC+3) · Open to senior full-stack, IoT and platform roles ·
[koomekoome902@gmail.com](mailto:koomekoome902@gmail.com) · [DEV](https://dev.to/megalodon) ·
[LinkedIn](https://www.linkedin.com/in/cliffkoome/)

---

#### Selected work

| Project | What it is | Architecture worth a look | Stack |
|---|---|---|---|
| [**MatConnect**](https://github.com/cliffkoome/MatConnect) | Real-time matatu arrival display: GPS units in vehicles feed live ETAs and SMS alerts to passengers at stages. | Live telemetry ingestion kept apart from the relational system of record; a scheduled ETA worker computes traffic-aware arrivals and fans them out to clients and SMS; role-based access for passengers, fleet owners and admins. | Node.js, Express, MariaDB, Firebase RTDB, Google Maps, Africa's Talking |
| [**typeghast**](https://github.com/cliffkoome/typeghast) | A terminal typing game played while a coding agent works. Ghosts multiply as the agent's context window fills. | Tails agent session logs in real time, a local open-weight model (Gemma 4 via Ollama) turns them into text to type; nothing leaves the machine. [Write-up on DEV →](https://dev.to/megalodon/typeghast-a-typing-game-haunted-by-your-coding-agents-context-window-5hkn) | Go, Bubble Tea, Ollama |
| [**Zuri** (Agenti)](https://github.com/davidongora/Agenti) | An accessible voice, text and sign-language companion that operates the M-PESA app for blind, low-vision, Deaf and older users. | Everything that touches money stays on the phone; a policy engine gates every action (allow / confirm / hand off / deny); a redactor masks names, numbers and amounts before anything reaches a language model. | Flutter, Kotlin, Android Accessibility, MediaPipe, TFLite, Node.js |

#### How I approach system design

- **Put the trust boundary in the right place.** Decide early what must run on the device, on the edge or in the cloud. Zuri keeps payments on the phone; typeghast keeps the agent's session on the machine.
- **Separate the hot path from the system of record.** Telemetry, events and user-facing state each get the store that fits them.
- **Design for failure first.** Flaky networks, offline devices and duplicate events are the normal case, not an edge case.
- **Write the decision down.** I document the trade-offs I made and what I'd change at 10× scale, starting with MatConnect.

#### Now

- Re-architecting **MatConnect** for production scale: event-driven ingestion, a documented architecture and its trade-offs.
- Writing about what I build on [DEV](https://dev.to/megalodon).

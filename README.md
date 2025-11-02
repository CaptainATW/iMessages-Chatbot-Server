## **About**

**talk about it** is an asynchronous Python-based message processing system that bridges Apple's iMessage ecosystem with advanced AI models. Built on `asyncio` and leveraging native macOS automation, talk about it enables intelligent, context-aware conversations at scale.

### Key Features

- **Concurrent Processing**: Handles $n \leq 20$ simultaneous conversations with $O(1)$ latency overhead
- **Natural Interaction**: Multi-message responses split on `\n\n` delimiters with dynamic typing delays $\Delta t \in [1.0, 3.0]$ seconds based on message length
- **Smart Debouncing**: Processes only the most recent message when users send rapid sequences, with configurable $\tau = 0.3s$ debounce period
- **Persistent Memory**: SQLite-backed conversation history maintains context across sessions
- **Real-time Indicators**: Typing bubbles and read receipts via GUI automation

### Architecture

```
Message Detection → SQLite Polling (500ms)
AI Processing → Gemini API (concurrent, n=20)
Response Delivery → AppleScript Automation (serialized)
```

### Technical Stack

- **Runtime**: Python 3.8+ with `asyncio` event loop
- **AI Backend**: Google Gemini 2.5 Flash via official SDK
- **Message I/O**: Direct SQLite access (`chat.db`) + AppleScript automation
- **Concurrency Model**: Semaphore-limited AI calls with GUI lock for serialization

### Performance Metrics

| Metric | Value |
|--------|-------|
| Optimal Capacity | 15-20 concurrent users |
| Internal Latency | $< 2s$ (excluding AI processing) |
| AI Response Time | $\mu = 1.5s$, $\sigma = 0.8s$ |
| Message Throughput | ~10-15 msg/min sustained |

---

## **Use Cases**

- **Therapy Assistance**: 24/7 mental health support via familiar messaging interface
- **Customer Service**: Automated support through business iMessage numbers
- **Personal AI Assistant**: Contextualized help accessible through text messages
- **Educational Tutoring**: On-demand learning support via SMS/iMessage

# Empathy LLM Toolkit

**Wrap any LLM with the Empathy Framework's 5 levels of AI-human collaboration.**

Transform your LLM from reactive Q&A (Level 1) to anticipatory partner (Level 4) automatically.

---

## Quick Start

```python
from empathy_llm import EmpathyLLM

# Initialize with any provider
llm = EmpathyLLM(
    provider="anthropic",      # or "openai", "local"
    target_level=4,            # Target: Anticipatory
    api_key="your-api-key"
)

# Interact - LLM automatically progresses through levels
response = await llm.interact(
    user_id="developer_123",
    user_input="Help me optimize this code",
    context={"code_snippet": "..."}
)

print(response["content"])
print(f"Level used: {response['level_used']}")  # Progresses: 1 → 2 → 3 → 4
```

---

## The 5 Levels

| Level | Behavior | When Activated |
|-------|----------|----------------|
| **1: Reactive** | Simple Q&A | Always (default) |
| **2: Guided** | Asks clarifying questions | Immediate |
| **3: Proactive** | Acts on patterns | After patterns detected + trust > 0.6 |
| **4: Anticipatory** | Predicts bottlenecks | After history + trust > 0.7 |
| **5: Systems** | Cross-domain learning | After trust > 0.8 |

**Key**: System automatically progresses based on collaboration state.

---

## Installation

```bash
pip install empathy-llm-toolkit

# Provider dependencies
pip install anthropic  # For Anthropic/Claude
pip install openai     # For OpenAI/GPT
# Local models work with no extra deps
```

---

## Providers Supported

### Anthropic (Claude)

```python
llm = EmpathyLLM(
    provider="anthropic",
    model="claude-3-5-sonnet-20241022",  # or opus, haiku
    api_key="sk-ant-..."
)
```

### OpenAI (GPT)

```python
llm = EmpathyLLM(
    provider="openai",
    model="gpt-4-turbo-preview",  # or gpt-3.5-turbo
    api_key="sk-..."
)
```

### Local Models (Ollama, LM Studio)

```python
llm = EmpathyLLM(
    provider="local",
    model="llama2",
    endpoint="http://localhost:11434"  # Ollama default
)
```

---

## Level Progression Examples

### Level 1: Reactive (First Interaction)

```python
# First interaction - always starts at Level 1
response = await llm.interact(
    user_id="user_1",
    user_input="What is Python?"
)

# Level 1: Direct answer
# "Python is a high-level programming language..."
```

### Level 2: Guided (Immediate)

```python
# Second interaction - progresses to Level 2
response = await llm.interact(
    user_id="user_1",
    user_input="Help me build an API"
)

# Level 2: Asks clarifying questions
# "I can help! A few questions:
#  1. What framework? (Flask, FastAPI, Django?)
#  2. What does the API do?
#  3. Any auth requirements?"
```

### Level 3: Proactive (After Patterns Detected)

```python
# Pattern detected: User always asks for tests after code
llm.add_pattern(
    user_id="user_1",
    pattern=UserPattern(
        pattern_type=PatternType.SEQUENTIAL,
        trigger="wrote code",
        action="requests tests",
        confidence=0.85,
        occurrences=5,
        last_seen=datetime.now()
    )
)

# Mark previous interactions as successful (builds trust)
llm.update_trust("user_1", "success")
llm.update_trust("user_1", "success")
llm.update_trust("user_1", "success")

# Now at Level 3!
response = await llm.interact(
    user_id="user_1",
    user_input="I just wrote the login function"
)

# Level 3: Proactively generates tests
# "I've detected you typically request tests after writing code.
#  I've proactively generated pytest tests for your login function:
#  [test code]
#  Was this helpful?"
```

### Level 4: Anticipatory (After History + High Trust)

```python
# After 10+ interactions and trust > 0.7
response = await llm.interact(
    user_id="user_1",
    user_input="I'm adding a 15th API endpoint"
)

# Level 4: Predicts future bottleneck
# "Your API now has 15 endpoints. Based on trajectory analysis:
#
#  ALERT: In our experience, API testing becomes bottleneck around
#  20+ endpoints without automation.
#
#  Prevention steps:
#  1. Implement integration test framework
#  2. Add API contract testing
#  3. Set up automated test generation
#
#  Would you like me to design this now while you have time?"
```

---

## Managing Trust

Trust determines how proactive the system becomes:

```python
# After successful interaction
llm.update_trust("user_1", "success")  # +0.05

# After failed/unhelpful interaction
llm.update_trust("user_1", "failure")  # -0.10 (erodes faster)

# Check trust level
stats = llm.get_statistics("user_1")
print(f"Trust: {stats['trust_level']:.0%}")
```

**Trust Thresholds**:
- 0.0-0.6: Stay at Level 2 (ask before acting)
- 0.6-0.7: Progress to Level 3 (proactive)
- 0.7+: Progress to Level 4 (anticipatory)
- 0.8+: Progress to Level 5 (systems)

---

## Pattern Detection

### Automatic Pattern Detection (Coming Soon)

```python
# Will automatically detect patterns from conversation history
await llm.detect_patterns("user_1")
```

### Manual Pattern Addition

```python
from empathy_llm import UserPattern, PatternType

# Add observed pattern
llm.add_pattern(
    user_id="developer_1",
    pattern=UserPattern(
        pattern_type=PatternType.SEQUENTIAL,
        trigger="makes code change",
        action="runs tests",
        confidence=0.90,
        occurrences=12,
        last_seen=datetime.now(),
        context={"framework": "pytest"}
    )
)
```

### Pattern Types

- `SEQUENTIAL`: User always does X then Y
- `TEMPORAL`: User does X at specific time
- `CONDITIONAL`: When Z happens, user does X
- `PREFERENCE`: User prefers format/style X

---

## Context Management

### Provide Context

```python
response = await llm.interact(
    user_id="user_1",
    user_input="Optimize this function",
    context={
        "code_snippet": "def slow_func()...",
        "performance_metrics": {...},
        "constraints": ["must be backwards compatible"]
    }
)
```

### Access Conversation History

```python
state = llm.states["user_1"]
history = state.get_conversation_history(max_turns=10)
```

---

## Force Specific Level (Testing/Demos)

```python
# Force Level 4 for demo
response = await llm.interact(
    user_id="demo_user",
    user_input="Show anticipatory analysis",
    force_level=4
)
```

---

## Statistics & Monitoring

```python
stats = llm.get_statistics("user_1")

print(f"""
User: {stats['user_id']}
Session Duration: {stats['session_duration']:.0f}s
Total Interactions: {stats['total_interactions']}
Trust Level: {stats['trust_level']:.0%}
Success Rate: {stats['success_rate']:.0%}
Patterns Detected: {stats['patterns_detected']}
Current Level: {stats['current_level']}
Average Level: {stats['average_level']:.1f}
""")
```

---

## Level 5: Cross-Domain Learning

```python
# Initialize with shared pattern library
shared_patterns = {
    "testing_bottleneck": {
        "source_domain": "software",
        "principle": "Manual processes become bottleneck at growth threshold",
        "applicable_to": ["healthcare_docs", "financial_compliance"],
        "threshold": "~20-25 items"
    }
}

llm = EmpathyLLM(
    provider="anthropic",
    target_level=5,
    pattern_library=shared_patterns
)

# LLM can now apply software patterns to other domains
response = await llm.interact(
    user_id="healthcare_user",
    user_input="We have 18 clinical documentation templates",
    force_level=5
)

# Applies software testing pattern to healthcare:
# "Pattern from software development applies here:
#  'Manual process bottleneck threshold'.
#
#  In software, manual testing becomes bottleneck at 20-25 tests.
#  Your 18 clinical templates suggest similar trajectory.
#
#  Alert: Consider template automation before burden compounds."
```

---

## Cost Optimization

### Use Tiered Models

```python
# Detection: Cheap model
detection_llm = EmpathyLLM(
    provider="anthropic",
    model="claude-3-haiku",  # Fast, cheap
    target_level=3
)

# Analysis: Smart model
analysis_llm = EmpathyLLM(
    provider="anthropic",
    model="claude-3-5-sonnet",  # Balanced
    target_level=4
)

# Critical: Best model (rare)
critical_llm = EmpathyLLM(
    provider="anthropic",
    model="claude-3-opus",  # Most capable
    target_level=5
)
```

### Monitor Costs

```python
response = await llm.interact(...)

tokens = response["metadata"]["tokens_used"]
model_info = llm.provider.get_model_info()

cost = (tokens / 1_000_000) * (
    model_info["cost_per_1m_input"] + model_info["cost_per_1m_output"]
) / 2  # Rough average

print(f"Cost: ${cost:.4f}")
```

---

## Healthcare Example

```python
llm = EmpathyLLM(provider="anthropic", target_level=4)

# Level 1: Basic SOAP note
response = await llm.interact(
    user_id="clinician_1",
    user_input="Generate SOAP note"
)

# After patterns detected + trust built...

# Level 3: Proactive pre-population
response = await llm.interact(
    user_id="clinician_1",
    user_input="Seeing patient John Doe"
)
# "I've detected you typically document vitals, allergies, meds.
#  I've pre-populated from EHR:
#  - Vitals: [data]
#  - Allergies: [data]
#  - Current meds: [data]"

# Level 4: Anticipatory compliance
response = await llm.interact(
    user_id="clinician_1",
    user_input="How are my notes looking?"
)
# "Analyzed last 50 notes. Joint Commission audit likely in ~90 days.
#  3 patterns will fail audit:
#  1. 12% missing required elements
#  2. Med reconciliation incomplete in 8 notes
#  I've flagged at-risk notes for review."
```

---

## Best Practices

### 1. Start Simple, Progress Naturally

```python
# Don't force Level 4 immediately
llm = EmpathyLLM(target_level=4)  # Good - progresses automatically

# Let trust build organically
for interaction in user_interactions:
    response = await llm.interact(...)
    if user_satisfied:
        llm.update_trust(user_id, "success")
```

### 2. Provide Rich Context

```python
# Bad: Minimal context
await llm.interact(user_id, "optimize code")

# Good: Rich context
await llm.interact(
    user_id,
    "optimize code",
    context={
        "code": code_snippet,
        "current_performance": metrics,
        "constraints": ["must work in Python 3.8+"],
        "goal": "reduce latency by ~30%"
    }
)
```

### 3. Monitor Trust and Adjust

```python
stats = llm.get_statistics(user_id)

if stats['success_rate'] < 0.7:
    # Too many failures - system being too aggressive
    llm.states[user_id].trust_level = 0.5  # Reset to cautious
```

### 4. Use Appropriate Provider for Task

```python
# Simple Q&A: GPT-3.5 (cheap)
simple_llm = EmpathyLLM(provider="openai", model="gpt-3.5-turbo")

# Complex analysis: Claude Sonnet
complex_llm = EmpathyLLM(provider="anthropic", model="claude-3-5-sonnet-20241022")

# Critical decisions: GPT-4 or Claude Opus
critical_llm = EmpathyLLM(provider="anthropic", model="claude-3-opus-20240229")
```

---

## Debugging

### Enable Logging

```python
import logging
logging.basicConfig(level=logging.INFO)

# See level progression and trust updates
llm = EmpathyLLM(...)
```

### Reset State

```python
# Reset user's collaboration state
llm.reset_state("user_1")
```

### Inspect State

```python
state = llm.states["user_1"]
print(f"Trust: {state.trust_level}")
print(f"Patterns: {len(state.detected_patterns)}")
print(f"Interactions: {len(state.interactions)}")
```

---

## API Reference

### EmpathyLLM

**`__init__(provider, target_level, api_key, model, pattern_library, **kwargs)`**
- Initialize with provider and target empathy level

**`async interact(user_id, user_input, context, force_level)`**
- Main interaction method
- Returns: `{"content": str, "level_used": int, "proactive": bool, "metadata": dict}`

**`update_trust(user_id, outcome, magnitude)`**
- Update trust based on interaction outcome
- `outcome`: "success" or "failure"

**`add_pattern(user_id, pattern)`**
- Manually add detected pattern

**`get_statistics(user_id)`**
- Get collaboration stats

**`reset_state(user_id)`**
- Reset user's state

---

## Related Resources

- **[Empathy Framework Documentation](../docs/CHAPTER_EMPATHY_FRAMEWORK.md)**
- **[Using Empathy with LLMs Guide](../docs/USING_EMPATHY_WITH_LLMS.md)**
- **[AI Development Wizards](../docs/AI_DEVELOPMENT_WIZARDS.md)**

---

## License

Apache License 2.0

---

**Built from experience. Shared with honesty. Extended by community.**

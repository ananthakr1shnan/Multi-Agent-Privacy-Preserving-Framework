# MPPF Decision Points & Conditional Flows

## 🔀 Critical Decision Points in MPPF Workflow

### 1. **Domain Classification → Aggressive Privacy Mode**

**Location**: After Domain Expert classification

**Decision Logic**:
```
IF domain IN ["Healthcare & Medical", "Privacy & Data Security", "Financial & Business"]
THEN activate Aggressive Privacy Mode
ELSE use Standard Privacy Mode
```

**Impact**:
- **Aggressive Mode**: Lower confidence thresholds, more PII patterns detected
- **Standard Mode**: Balanced detection, fewer false positives

**Visual Representation**:
```
Domain Expert
    ↓
  [Decision Diamond]
  "High-Risk Domain?"
    ↓
   / \
YES    NO
 ↓      ↓
Aggressive  Standard
Privacy     Privacy
```

**Example**:
- Healthcare query → Aggressive → Detects SSN, Medical IDs
- General query → Standard → Only standard PII

---

### 2. **Ethics Agent Veto Power**

**Location**: After Agent processing, before Aggregator

**Decision Logic**:
```
IF Ethics Agent flags response as unsafe
THEN override all other agents and return safe default
ELSE proceed to weighted aggregation
```

**Impact**:
- Ethics agent can **completely override** other agents
- Activated in sensitive domains (Healthcare, Finance)

**Visual Representation**:
```
Ethics Agent Response
    ↓
  [Decision Diamond]
  "Safety Veto?"
    ↓
   / \
YES    NO
 ↓      ↓
Return    Proceed to
Safe      Aggregator
Default   (weighted)
```

**Example**:
- Ethics flags medical advice → Returns "Please consult a doctor"
- Ethics approves → Aggregates all 3 responses

---

### 3. **Domain-Adaptive Weighting**

**Location**: Aggregator synthesis

**Decision Logic**:
```
CASE domain OF
  "Healthcare & Medical":
    weights = {Ethics: 50%, Productivity: 30%, Creativity: 20%}
  
  "Financial & Business":
    weights = {Ethics: 40%, Productivity: 40%, Creativity: 20%}
  
  "Creative & Arts":
    weights = {Creativity: 50%, Productivity: 30%, Ethics: 20%}
  
  DEFAULT:
    weights = {Productivity: 40%, Ethics: 35%, Creativity: 25%}
END CASE
```

**Visual Representation**:
```
Domain Classification
    ↓
[Decision Tree]
Healthcare? → Ethics 50%
Finance?    → Balanced 40/40/20
Creative?   → Creativity 50%
Other?      → Productivity 40%
    ↓
Apply weights to aggregation
```

---

### 4. **Context Availability Check**

**Location**: Retriever (RAG) node

**Decision Logic**:
```
IF ChromaDB returns chunks with similarity > threshold (0.7)
THEN use retrieved context
ELSE proceed without additional context (LLM's base knowledge only)
```

**Impact**:
- With context: More accurate, domain-specific answers
- Without context: General knowledge response

**Visual Representation**:
```
Retriever Query
    ↓
  [Decision Diamond]
  "Relevant Context Found?"
  (similarity > 0.7)
    ↓
   / \
YES    NO
 ↓      ↓
Include   Use LLM
Context   Base Knowledge
    ↓      ↓
    └──┬───┘
       ↓
   Send to Agents
```

---

### 5. **Privacy Budget Availability**

**Location**: Before Differential Privacy application

**Decision Logic**:
```
IF privacy_budget_remaining >= query_epsilon
THEN apply DP noise and deduct from budget
ELSE reject query OR reset budget
```

**Visual Representation**:
```
Before DP Application
    ↓
  [Decision Diamond]
  "Budget Available?"
  (remaining ≥ ε)
    ↓
   / \
YES    NO
 ↓      ↓
Apply   Reject Query
DP      OR
Noise   Reset Budget
       (daily/hourly)
```

**Example**:
- Budget: 1.0, Query needs 0.3 → Proceed (remaining: 0.7)
- Budget: 0.1, Query needs 0.3 → Reject or reset

---

### 6. **Redaction Count Threshold**

**Location**: Privacy Shield output validation

**Decision Logic**:
```
IF redaction_count > threshold (e.g., 10)
THEN flag as "Highly Sensitive" AND log warning
ELSE proceed normally
```

**Impact**:
- High redaction count → Extra scrutiny
- May trigger additional audit logging

**Visual Representation**:
```
Privacy Shield Complete
    ↓
  [Decision Diamond]
  "Redaction Count > 10?"
    ↓
   / \
YES    NO
 ↓      ↓
Flag as  Continue
High     Normally
Sensitivity
```

---

## 🎨 Complete Workflow with Decision Points

### Enhanced Diagram Structure

```
┌─────────────────────────────────────────────────────┐
│ Stage 1: User Input (RED)                           │
│ "Email john@example.com about medical record M123"  │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ Stage 2: Privacy Shield (BLUE BOX - HIGHLIGHTED)    │
│ - Presidio + spaCy detection                        │
│ - Output: "Email <EMAIL> about medical record       │
│           <MEDICAL_ID>"                              │
└──────────────────┬──────────────────────────────────┘
                   ↓
         ┌─────────┴─────────┐
         ↓                   ↓
┌──────────────────┐  ┌──────────────────┐
│ Domain Expert    │  │ Retriever (RAG)  │
│ Classification   │  │ ChromaDB Query   │
└────────┬─────────┘  └────────┬─────────┘
         │                     │
         ↓                     ↓
    ◆ DECISION 1           ◆ DECISION 2
    "Healthcare            "Context Found?"
     Domain?"              (similarity > 0.7)
         ↓                     ↓
    YES → Aggressive      YES → Include Context
    Privacy Mode          NO → Base Knowledge
         ↓                     ↓
         └─────────┬───────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ Stage 3: Multi-Agent Processing (GREEN)             │
│                                                      │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│ │ Productivity │ │   Ethics     │ │  Creativity  │ │
│ │    Agent     │ │   Agent      │ │    Agent     │ │
│ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ │
│        │                │                │         │
│        └────────────────┼────────────────┘         │
└─────────────────────────┼──────────────────────────┘
                          ↓
                     ◆ DECISION 3
                   "Ethics Veto?"
                          ↓
                     YES / NO
                      ↓     ↓
              Safe Default  Aggregator
                      ↓         ↓
                      └────┬────┘
                           ↓
                      ◆ DECISION 4
                "Domain-Based Weighting"
                  Healthcare → Ethics 50%
                  Finance → Balanced
                  Creative → Creativity 50%
                           ↓
┌─────────────────────────────────────────────────────┐
│ Stage 4: Aggregator Synthesis (GOLD)                │
│ - Weighted combination                              │
│ - LLM-based synthesis                               │
└──────────────────┬──────────────────────────────────┘
                   ↓
              ◆ DECISION 5
           "Privacy Budget OK?"
          (remaining ≥ ε)
                   ↓
              YES / NO
               ↓     ↓
          Apply DP  Reject/
          Noise     Reset
               ↓
┌─────────────────────────────────────────────────────┐
│ Stage 5: Differential Privacy (ORANGE)              │
│ - Add Laplacian noise (ε=1.0)                       │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ Stage 6: Audit Logger (GRAY)                        │
│ - Store anonymized query + metadata                 │
└──────────────────┬──────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────┐
│ Stage 7: Final Response (GREEN)                     │
│ "Your medical record request has been processed..."  │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Decision Point Summary Table

| # | Decision Point | Location | Condition | Impact |
|---|----------------|----------|-----------|---------|
| **1** | Aggressive Privacy Mode | After Domain Expert | High-risk domain? | More/fewer PII detections |
| **2** | Context Inclusion | Retriever output | Similarity > 0.7? | Use KB context or not |
| **3** | Ethics Veto | After Ethics Agent | Safety flag? | Override response |
| **4** | Domain Weighting | Aggregator | Domain type? | Agent weight distribution |
| **5** | Privacy Budget | Before DP | Budget available? | Apply noise or reject |
| **6** | High Sensitivity Flag | Privacy Shield | Redactions > 10? | Extra logging |

---

## 🎯 For Your Diagram

### Visual Elements to Add:

1. **Decision Diamonds** (◆) - Use diamond shapes for all decision points
2. **Conditional Arrows** - YES/NO branches clearly labeled
3. **Color Coding**:
   - Red paths: High-risk/rejected flows
   - Green paths: Approved/normal flows
   - Yellow paths: Warning conditions

4. **Annotations**:
   - Add small text boxes explaining each decision
   - Example: "Ethics veto in healthcare queries"

5. **Feedback Loops** (if showing):
   - Budget reset (daily/hourly)
   - Model retraining based on vetoes

---

## 🔍 Example Conditional Flows

### Flow 1: Healthcare Query with Veto

```
Input: "Patient John Doe SSN 123-45-6789"
  ↓
Privacy Shield → Redaction count: 2 (Name + SSN)
  ↓
Domain Expert → "Healthcare & Medical"
  ↓
DECISION: Aggressive Mode → YES
  ↓
(Re-scan with aggressive patterns)
  ↓
Agents Process
  ↓
Ethics Agent → VETO (medical advice detected)
  ↓
DECISION: Ethics Veto? → YES
  ↓
Output: "Please consult a doctor for medical advice"
```

### Flow 2: General Query, No Context

```
Input: "What's the weather like?"
  ↓
Privacy Shield → Redaction count: 0
  ↓
Domain Expert → "General Inquiry"
  ↓
DECISION: Aggressive Mode → NO
  ↓
Retriever → No relevant context (similarity: 0.2)
  ↓
DECISION: Context Found? → NO
  ↓
Agents use base knowledge only
  ↓
Aggregator → Default weights (40/35/25)
  ↓
DP applied → Output with noise
```

---

## ✅ Updated Diagram Prompt

Add these decision points to your original prompt:

```
**Decision Points to Highlight:**

1. After Domain Expert:
   Diamond: "High-Risk Domain?"
   - YES → Aggressive Privacy Mode
   - NO → Standard Mode

2. After Retriever:
   Diamond: "Relevant Context Found? (similarity > 0.7)"
   - YES → Include context chunks
   - NO → Base knowledge only

3. After Ethics Agent:
   Diamond: "Safety Veto Triggered?"
   - YES → Return safe default response
   - NO → Proceed to aggregation

4. At Aggregator:
   Decision Tree: "Domain-Based Weighting"
   - Healthcare → Ethics 50%
   - Finance → Balanced 40/40/20
   - Creative → Creativity 50%
   - Default → Productivity 40%

5. Before DP:
   Diamond: "Privacy Budget Available?"
   - YES → Apply noise, deduct budget
   - NO → Reject query or reset budget

**Visual Style for Decisions:**
- Use orange/yellow diamond shapes
- Label YES/NO paths clearly
- Add dotted lines for conditional flows
- Use solid lines for guaranteed flows
```

---

**These decision points make your system more sophisticated and show the intelligent routing logic!** 🎯

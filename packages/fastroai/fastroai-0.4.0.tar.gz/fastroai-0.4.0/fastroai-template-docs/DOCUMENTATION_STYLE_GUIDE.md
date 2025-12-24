# FastroAI Documentation Style Guide

**Write like you're explaining to a colleague - direct, practical, experienced.**

This guide establishes the rules and guidelines for writing FastroAI documentation that sounds human, not AI-generated.

## 🗣️ Conversational Tone Rules

### Write Like a Human
- **Write like you're explaining to a colleague** - direct, practical, experienced
- **Use contractions and casual language** - "you'll," "don't," "it's"
- **Add personality without being unprofessional** - "Poof. The `/admin` endpoint disappears."
- **Give practical advice from experience** - "Tag your git repo before removing features"

### Avoid AI-Generated Language Patterns
- **No corporate speak** - avoid "modular by design," "the pattern is always the same," "seamlessly integrates"
- **No marketing language** - avoid "revolutionary," "cutting-edge," "powerful platform"
- **No repetitive AI phrases** - avoid "What happens:", "The bottom line", "Here's the thing"
- **No templated section titles** - "Use What You Need" not "The Bottom Line"
- **No grandiose descriptions** - avoid "the beauty of this design," "orchestrates everything"
- **No artificial emphasis phrases** - avoid "Here's the key insight:", "What's really powerful here is:", "The magic happens when:", "At the end of the day:"
- **No oversimplification words** - avoid "straightforward," "simply," "just," "easy"
- **No foundation metaphors** - avoid "The foundation is solid," "builds on a solid foundation"
- **No storytelling clichés** - avoid "Picture this:", "Imagine," "magic moment," "magic happens"
- **Use natural observations** - "Notice how" instead of "The beauty is"

## 📚 Content Guidelines

### Teaching-First Approach
- **Build understanding progressively** - each concept builds on the previous
- **Explain why before how** - give context for technical decisions  
- **Use a teaching mindset** - help users understand concepts, not just syntax
- **Start with concrete user scenarios** - Show Sarah's problem before showing solutions
- **Lead with problems, not features** - "Sarah needs X" before "Here's how to configure Y"
- **Focus on practical scenarios** - when would you actually use this?
- **Connect each piece to user goals** - always tie back to how this helps solve the user's problem

### Conversational Flow
- **Use conversational paragraphs** - avoid excessive bullet lists
- **Natural transitions** - "This is where...", "Here's what happens when...", "The key insight here is..."
- **Bridge sections explicitly** - "Now we have X, but we need Y. Let's build that next."
- **Connect to previous work** - "using the config from earlier", "our agent from the previous section"
- **Direct engagement** - ask questions, use "you" and "we"
- **Build narrative** - connect concepts with story flow
- **Progressive disclosure** - introduce complexity gradually

### Technical Accuracy
- **Verify everything against codebase** - check actual variable names, defaults, features
- **Use real examples from actual codebase** - no fictional code snippets
- **Test configuration examples** - ensure all env vars actually exist
- **No fictional features** - only document what's implemented
- **Use correct file paths and code references** - `file_path:line_number` format
- **Honest about limitations** - explain trade-offs and constraints

### Code Explanation Style
- **Don't explain code in inline comments** - break code blocks into parts
- **Explain code with text between blocks** - use narrative to connect code sections
- **Show context before showing code** - explain what problem the code solves
- **Use real scenarios** - connect code examples to actual use cases
- **Make missing context explicit** - use comments like "(using the config from earlier)"
- **Right level of detail** - explain new concepts thoroughly, don't over-explain what FastroAI handles automatically
- **Component roles, not overstatements** - "coordinates between" not "orchestrates everything"
- **Break large code blocks into logical chunks** - don't dump 60+ lines at once
- **Explain FastroAI dependencies** - mention when using FastroAI-provided functions like `get_db_session`
- **Verify all imports** - ensure code examples include all necessary imports

### Backend Validation Philosophy
- **Frontend for UX, backend for security** - this is FastroAI's core principle
- **Always emphasize server-side validation** - frontend validation is just for user experience
- **Security-first mindset** - assume all client input is malicious

## 🎨 Component Usage

### Use Admonitions Sparingly
- **Tips for helpful extras** - git safety nets, optimization hints
- **Warnings for real dangers** - production considerations, breaking changes  
- **Notes for important context** - not just restatements
- **Don't wrap entire sections in boxes** - normal content should flow naturally

### Visual Organization
- **Cards for navigation and feature overviews** - helps users scan options
- **Tables for reference information** - configuration options, comparisons
- **Conversational paragraphs over bullet lists** - when explaining concepts
- **Avoid multiple boxes in a row** - breaks visual flow

## 🔧 Structure and Flow

### Content Organization
- **Clear headings without AI patterns** - sound human, not templated
- **Logical information hierarchy** - most important information first
- **Scannable content** - use headings, lists, and visual breaks appropriately

### Documentation Types
- **Getting Started** - action-focused, minimal theory, get users running immediately
- **Learning** - problem-driven, conceptual understanding, teach the why
- **Configuration** - comprehensive reference with practical context
- **Features** - conversational explanation of what and why

## ❌ What to Avoid

### Visual Elements
- **Emojis in content** (✅❌) - use semantic components instead
- **Excessive bullet points** - use conversational paragraphs when explaining
- **Wall of admonition boxes** - sparingly means sparingly

### Language Patterns
- **"What happens:" patterns** - integrate explanations naturally into flow
- **Stating the obvious** - don't list features users can already see
- **Hypothetical examples** - use real code from the project
- **Generic advice** - be specific to FastroAI's implementation

## 📖 Documentation Examples

### Good: Conversational and Practical
```markdown
Building a prototype? Don't want to deal with Redis right now?

```env
CACHE_ENABLED=false
RATE_LIMITER_ENABLED=false
```

Done. FastroAI skips Redis entirely. Rate limiting falls back to memory 
(which works fine if you're running a single process).
```

### Good: Problem-Driven with Transitions
```markdown
Sarah needs specific behavior from our financial assistant: accurate calculations, 
encouraging but realistic advice, and responses she can understand and act on. 
Let's translate these requirements into agent configuration.

Our agent has configuration and tools, but there's one more piece needed for a 
good user experience: conversation memory. Let's add that next.
```

### Bad: AI-Generated Language
```markdown
## The Bottom Line

FastroAI is modular by design. The pattern is always the same:
1. Disable via configuration first
2. Test everything still works  
3. Remove code only if you really want to

**What happens:** Rate limiting switches to in-memory mode.
```

### Good: Real Technical Context
```markdown
FastroAI uses sequential IDs instead of UUIDs for primary keys. Why? You have 
proper authentication, and for most applications, people knowing how many users 
you have doesn't really matter. Plus, it's not hard to migrate to UUIDs if 
distributed scaling becomes necessary.
```

### Bad: Generic Technical Advice
```markdown
FastroAI uses UUIDs everywhere for better scalability and security. This is 
a best practice that ensures your application can scale seamlessly.
```

## 🎯 Quality Checklist

Before publishing documentation, verify:

- [ ] Sounds like a human wrote it, not AI
- [ ] All code examples come from actual codebase  
- [ ] All configuration variables actually exist
- [ ] Technical claims are verified against implementation
- [ ] Uses FastroAI-specific context, not generic advice
- [ ] Admonitions used for actual warnings/tips, not content wrapper
- [ ] No more than one admonition box per section
- [ ] Practical examples with real scenarios
- [ ] Backend validation philosophy emphasized where relevant
- [ ] Sections connect with explicit transitions
- [ ] Code context is explained or referenced
- [ ] Component roles described accurately (not overstated)
- [ ] Problems explained before solutions
- [ ] New concepts taught thoroughly, automated features kept simple

## 📝 The Goal

Documentation that sounds like it was written by an experienced developer who actually uses FastroAI, not by a documentation generator or marketing team.

**Write for developers who want to ship products, not for people who want to read about features.**
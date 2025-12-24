# Case Study: Problem Identification

**From messy real-world problems to something specific we can solve.**

This is the first part of our Personal Finance Assistant case study. We'll work through taking a vague idea and turning it into something concrete we can actually build.

!!! tip "The Foundation Phase"
    Everything that follows - technical decisions, architecture choices, what to build first - depends on getting this part right. Skip the problem work and you'll build something nobody wants.

Too many AI projects rush straight into technical implementation because that's the fun part. But if you don't understand the actual problem you're solving, you'll end up with impressive technology that nobody uses. Let's do this right.

## Starting with the Raw Problem

Let's start with the messy, real-world problem statement: "People are bad with money and make poor financial decisions that hurt their long-term well-being."

That's way too broad to be actionable. We need to narrow it down to something specific we can actually solve. So let's work through this step by step.

**Who actually has this problem?**

We're talking about working adults with regular income who want to make better financial decisions but struggle with complexity, time constraints, or lack of expertise. This includes everyone from new graduates to established professionals who never learned proper financial management.

We're not talking about people in financial crisis or those who need debt counseling - we're focusing on people who have income but want to optimize how they manage it.

**What are they struggling with day-to-day?**

Understanding where their money goes each month, recognizing spending patterns that might be problematic, making informed decisions about savings and investments, planning for financial goals, and knowing when their financial behavior is helping or hurting them.

This creates a fundamental mismatch:

!!! note "The Core Problem"
    People are drowning in financial data but starving for insights on how to manage their money better.

Let's take a look at what this problem looks like in practice:

| What People Have | What People Need |
|------------------|------------------|
| Bank statements with transaction lists | Understanding of spending patterns |
| Credit card records with dates/amounts | Context: "Is this normal for me?" |
| Investment account balances | Progress tracking toward goals |
| Spreadsheets with raw numbers | Actionable insights and recommendations |
| **Data Rich** | **Insight Poor** |

This gap between having data and understanding it is where the opportunity lies. They have plenty of information - bank statements, credit card records, investment accounts - but they lack insights.

**How do they try to solve this today?**

Most use bank apps that show account balances but provide no context or analysis. Some try budgeting apps like Mint or YNAB that require significant setup and ongoing maintenance. A few attempt spreadsheets but lack the expertise. Others have occasional meetings with financial advisors that are expensive and don't address day-to-day questions.

And frequently, people simply ignore the problem and hope for the best.

Here's how the current landscape fails people:

<div class="grid cards" markdown>

-   :material-bank:{ .lg .middle } **Bank Apps**

    ---

    Shows $800 spent on dining. No context: Normal? Problem?

    **Result:** Data without understanding

-   :material-chart-line:{ .lg .middle } **Budgeting Apps**

    ---

    Mint/YNAB setup required. Manual categorization. Most people quit.

    **Result:** Too much work, people abandon

-   :material-file-table:{ .lg .middle } **Spreadsheets**

    ---

    Need Excel expertise. Time consuming. Easy to mess up.

    **Result:** Too complex for most people

-   :material-account-tie:{ .lg .middle } **Financial Advisors**

    ---

    $200+ per meeting. Focus on big decisions. Not daily questions.

    **Result:** Too expensive for everyday help

-   :material-calculator:{ .lg .middle } **Generic Finance Apps**

    ---

    Basic expense trackers. Simple categories. No personalization or insights.

    **Result:** Still just organizing data

-   :material-sleep:{ .lg .middle } **Do Nothing**

    ---

    Hope for the best. Problem gets worse over time.

    **Result:** Financial stress increases

</div>

**Why current solutions don't work well**

Bank apps are passive - they can tell you that you spent $800 on dining out but can't explain whether that's normal, problematic, or related to specific events. Budgeting apps require users to manually categorize every transaction and maintain complex category systems that most people abandon after a few weeks. Financial advisors are expensive and not accessible for smaller financial questions. Spreadsheets require expertise that most people don't want to develop.

Success would mean people making more informed financial decisions with less effort, understanding their financial patterns without becoming spreadsheet experts, feeling confident about their financial choices, and making progress toward their financial goals without the friction of current tools.

Based on this exploration, here's our refined problem statement:

**Working adults need personalized financial insights and guidance that help them understand their spending patterns and make better financial decisions, but current tools either provide raw data without context or require significant time investment to set up and maintain.**

Notice how this is much more specific than "people are bad with money." It identifies the target audience, describes the specific need, and explains why current solutions are inadequate.

## Checking If This Problem Actually Matters

Before getting excited about building anything, let's check that this is actually a problem worth solving.

The numbers suggest people struggle with this stuff. Financial stress affects 76% of Americans. The average American can't afford a $400 emergency expense. People consistently make poor financial decisions despite having access to information.

More importantly, people are already paying for solutions. Mint has over 20 million users. YNAB charges $84 annually with hundreds of thousands of subscribers. The financial advisory industry manages trillions in assets.

So there's definitely demand. The question is whether there's room for something different. Existing tools require significant user effort (YNAB), provide limited insights (bank apps), or are too expensive for everyday questions (financial advisors).

People check their bank accounts regularly but don't understand what the numbers mean for their financial health. They want financial guidance but find existing tools overwhelming or inadequate.

This suggests we've found a real problem with real demand and gaps in existing solutions.

## What's Already Out There

Let's look at existing solutions to see where they fall short and where there might be room for something different.

**Data aggregators like Mint and Personal Capital** are great at showing you what happened but terrible at explaining why or what to do about it. They give you category breakdowns and spending trends without context or personalization. They answer "What did I spend?" but not "What does this mean for my financial health?"

**Budgeting apps like YNAB** have strong methodology but demand significant commitment. They force users to manually categorize every transaction and maintain detailed budgets. Most people abandon them because they require behavior change upfront rather than gradually building engagement. They work for highly motivated users but fail for everyone else who wants insights without administrative overhead.

**Financial advisors** provide excellent personalized advice but cost hundreds of dollars per meeting and focus on long-term planning rather than immediate decisions. They're great for major financial choices but impractical for everyday questions like "Is my coffee spending reasonable?"

**Bank apps** show current data but provide zero intelligence. They know what you spent but can't explain patterns, compare to benchmarks, or suggest improvements. They're essentially digital versions of paper statements.

**Robo-advisors** handle investment management well but ignore day-to-day financial behavior. They don't address spending patterns, saving strategies, or the behavioral aspects of money management.

The gap is clear: people want natural language interaction combined with personalized insights based on their individual spending patterns. Something with lower barriers than budgeting apps, more accessible than human advisors, more intelligent than bank apps, and more actionable than basic data aggregation.

## Who Would Actually Use This

Let's get concrete about what users actually need. Here are our target users and what they're looking for:

| User Profile | Primary Pain Point | Current Solution | Desired Outcome |
|--------------|-------------------|------------------|-----------------|
| **Alex, 31<br>Teacher** | "Get to end of month with $0, don't know where money goes" | Looks at bank data but gets overwhelmed, doesn't grasp how small spending adds up | Understand where money actually goes and identify spending drains |
| **Sarah, 28<br>Marketing Manager** | "I make decent money but never have enough saved" | Check bank apps, feel confused by numbers | Understand spending patterns without complexity |
| **Mike, 35<br>Small Business Owner** | "Variable income makes traditional budgeting impossible" | Worry and guess about sustainability | Guidance that accounts for irregular income |
| **Jennifer, 42<br>Working Parent** | "Don't know if I'm on track for major goals" | Generic online advice, conflicting information | Specific guidance for her situation |

Each of these stories reveals the same core need: personalized guidance delivered in an accessible way. These aren't problems you solve with static content or simple calculations - they need the kind of contextual understanding and adaptive communication that LLMs provide.

## What We're Actually Building

Based on this analysis, we can define what we're actually trying to build:

!!! success "Our Value Proposition"
    Get personalized financial insights and guidance through natural conversation, without the complexity of traditional budgeting apps or the cost of financial advisors.

This value proposition directly addresses the gaps we identified: existing tools are either too complex, too expensive, or too limited. None provide the combination of personalization, accessibility, and intelligence that users need for day-to-day financial decisions.

## Where We Stand

We've worked through problem identification and validation. We understand who has this problem, why current solutions fail, and what success would look like.

This foundation shapes every technical decision that follows. Now we need to figure out whether AI is actually the right tool for this job.

[Continue to Technical Design →](technical-design.md){ .md-button .md-button--primary }

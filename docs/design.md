# AI Interview Prep Platform MVP

Design a personalised AI powered coaching platform for preparing for interviews on any topic\.<br>Follow customised plans to do daily structured practice with real time feedback which adapts to your results and continually focus on weak &#x2F; missing areas\.

## Requirements

### Functional:

- Users can create an account
- Users interact with llms through a framework layer that informs llms in which way to respond and which actions to take at different stages
- Users can interact via typing or dictating
- Users can collaborate with llms to produce a structured training plan for practicing for interviews\. Llms will prompt for following information to inform plan:<br>\- role applying to \(SWE, sales, marketing, teaching etc\.\.\)<br>\- time available to spend on studying<br>\- perceived areas of weakness<br>\- self assessment on capacity to study \(motivation\)<br>LLMS will suggest a plan broken down into categories and time to spend studying each day
- Users can view the study plan broken down into sessions
- Users can interact with llm to adjust plan
- Users can start study sessions based on plan with timer<br>\- platform will suggest session to do but user can choose different session if desired<br>\- llms will suggest questions \(either practiced or new\), users can choose which to answer<br>\- users can either generate a story structure with llm or practice answering<br>\- users will be timed when answering questions<br>\- llms will save story structures for questions in a file that can be accessed and edited by users<br>\- Users can skip questions
- A reconcilliation process will run after each study session<br>\- llms will summarise questions practiced with marks on answers<br>\- llms will adjust a context file tracking user progress on each topic, it will plan the next questions to focus on
- either when a user logs in or presses a button, a process will run which evaluates total user progress and suggests adjustments to the plan \(e\.g\. spend more time on x, less on y\)\.<br>Max once per day

### Out of scope:

- Calendar display and interactions
- Library of stories
- Progress analytics
- Custom achievements, trophies and goals
- Gamification functionality
- Searching for new jobs
- CV &#x2F; cover letter writing
- Real time conversations &#x2F; real time spoken answer analysis \(delivery, vocal fluff, pauses, tone\)

### Non Functional:

- Consistency &gt; availibility for MVP
- No hard latency requirement on api requests to LLMs since answer time is slow already \(&lt;1s\)
- Scalable to 1k users
- 50 users simultaneously
- User context and chats must be secure &#x2F; encrypted
- explainability \- llms must explain changes to plan and have them be approved
- graceful degradation \- if llm fails, session is not lost and user can retry

## Core Entities:

- user<br>\- name<br>\- current applying role
- PlanTopic<br>\- name<br>\- description<br>\- planned daily study time<br>\- priority
- TopicProgress<br>\- topic id<br>\- strength rating<br>\- total time spent 
- StudySession<br>\- topic id<br>\- planned\_duration<br>\- start time<br>\- last\_interaction\_time<br>\- end time
- RawUserContext<br>\- User story no formatting &#x2F; processing, just all the details of the users experience 
- Question<br>\- question<br>\- answer anchors<br>\- topic id
- QuestionAttempt<br>\- question id<br>\- study session id<br>\- raw answer<br>\- score rating<br>

## APIs:

Plan = PlanTopic\[\]

- POST &#x2F;users&#x2F;create =&gt; redirect to home page<br>body: \{username, password\}
- POST &#x2F;users&#x2F;login =&gt; redirect to home page<br>body: \{username, password\}
- POST &#x2F;plan&#x2F;suggest\_new =&gt; Plan<br>body: \{role applying for, raw user context\}<br>llm generates a plan suggestion based on user role and any story the user tells about it
- POST &#x2F;plan&#x2F;suggest\_changes =&gt; Plan<br>body: \{raw user context, Plan, \(user feedback on plan\)\[\] ?, progress on plan topics?\}<br>llm analyses current plan \+ user feedback on plan\+ progress on plan so far and proproses a new plan 
- POST &#x2F;plan&#x2F;approve\_plan =&gt; 200<br>body: \{Plan\}<br>backend saves plan to db
- GET &#x2F;plan&#x2F;view =&gt; Plan
- POST &#x2F;study&#x2F;start\_session&#x2F; =&gt; TopicStudySession <br>body: \{topic\_id, planned\_study\_time\}<br>backend creates and inserts new TopicStudySession object, frontend navigates to session page, starts timer and calls generate\_questions
- PUT &#x2F;study&#x2F;end\_session&#x2F; =&gt; StudySession <br>body: \{session\_id\}<br>update end time in StudySession and trigger reconcilliation process in backend
- POST &#x2F;study&#x2F;generate\_questions&#x2F;\{session\_id\} =&gt; Question\[\]
- POST &#x2F;study&#x2F;evaluate\_answer&#x2F;\{session\_id\} =&gt; llm response and score<br>body: \{questionAttempt\}<br>

## LLM Modes:

Token per user per day figures are very rough upper range guesses which I use to estimate calculate costs per user per month\.

- SuggestPlan<br>inputs: \{role: 5 tokens, user context: 5000 tokens\}<br>calls &#x2F; user &#x2F; day: 0\.1<br>output: 200 tokens <br>schema: \{<br>  &quot;plan\_overview&quot;: \{<br>    &quot;target\_role&quot;: &quot;string&quot;,<br>    &quot;total\_daily\_minutes&quot;: &quot;int&quot;,<br>    &quot;time\_horizon\_weeks&quot;: &quot;int&quot;,<br>    &quot;rationale&quot;: &quot;string \(max 60 words\)&quot;<br>  \},<br>  &quot;plan\_topics&quot;: \[<br>    \{<br>      &quot;name&quot;: &quot;string \(max 3 words\)&quot;,<br>      &quot;description&quot;: &quot;string \(max 20 words\)&quot;,<br>      &quot;priority&quot;: &quot;int \(1 = highest priority\)&quot;,<br>      &quot;daily\_study\_minutes&quot;: &quot;int&quot;,<br>      &quot;expected\_outcome&quot;: &quot;string \(max 15 words\)&quot;<br>    \}<br>  \]<br>\}
- SuggestPlanChanges<br>inputs: \{currentPlan: 200 tokens, role: 5 tokens, user context: 5000 tokens, current progress: 100 tokens\}<br>calls &#x2F; user &#x2F; day: 0\.5<br>output: 200 tokens<br>schema: same as above
- GenerateQuestions<br>inputs: \{previously asked questions and ratings: 2000 tokens\}<br>calls &#x2F; user &#x2F; day: 5<br>output: 300 tokens<br>schema: \{<br>  &quot;questions&quot;: \[<br>    \{<br>      &quot;question&quot;: &quot;string \(max 30 words\)&quot;,<br>      &quot;status&quot;: &quot;new | redo&quot;,<br>      &quot;redo\_reason&quot;: &quot;weak\_answer | incomplete | time\_pressure | high\_value&quot;,<br>      &quot;difficulty&quot;: &quot;easy | medium | hard&quot;<br>    \}<br>  \]<br>\}
- EvaluateAnswer<br>inputs: \{question: 100 tokens, answer: 1000 tokens, question context: 300 tokens\}<br>calls &#x2F; user &#x2F; day: 30<br>output: 500 tokens<br>schema: \{<br>  &quot;score&quot;: int \(1 very bad \- 10 very good\)<br>  &quot;positive feedback: string\[0\-3\] \(max 30 words per point\)<br>  &quot;improvement\_areas&quot;: string\[0\-3\] \(max 30 words per point\)<br> &quot;anchors&quot;: <br>  \[<br>   \{ <br>    &quot;name&quot;: string \(max 3 words\),<br>    &quot;anchor&quot;: text \(max 50 words\)<br>   \}<br>  \]<br>\}
- ReconcileSession<br>inputs: \{session question attempts: 10000 tokens\}<br>calls &#x2F; user &#x2F; day: 3<br>output: 1000 tokens<br>schema: \{<br>  QuestionAttempts: \[<br>  \{<br>   &quot;question&quot;: string \(max 30 words\),<br>   &quot;attempts&quot;: int,<br>   &quot;best\_score&quot;: int \(1\-10\),<br>   &quot;best\_anchors&quot;: <br>    \[<br>     \{ <br>      &quot;name&quot;: string \(max 3 words\),<br>      &quot;anchor&quot;: text \(max 50 words\)<br>     \}<br>    \],<br>   <br>  \}<br> \]<br>\}

total input tokens &#x2F; user &#x2F; day = 85k

total output tokens &#x2F; user &#x2F; day = 20k<br>costs range from 30c to 100$ per month and this is heavily optimisable

### Stack

- **Backend:** FastAPI
- **DB:** Postgres
- **ORM:** SQLAlchemy
- **Frontend:** Next\.js
- **LLM SDK:** Python \(OpenAI &#x2F; Anthropic &#x2F; etc\.\)


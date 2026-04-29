## README

1. Project Title
   - Short descriptive title
   - One-sentence tagline

   Guessing Game with AI Helper!
   Try to guess the magic number but don't fear if you get stuck, because AI is there to help.

2. Original Project Summary
   - Name of original project
   - 2-3 sentence summary of original goals and capabilities

   Old Name: Game Glitch Investigator 
   The original game was a number guessing game where players try to guess a secret number with the ability to change the difficulty level. The difficulty level determines the range the number that is to be guessed is picked between so for example easy is 1 - 20 while hard might be 1-100.

3. What It Does
   - High-level explanation of current app
   - Why it matters / what problem it solves

   The current app has the same logic as mentioned above except for one additional feature which is the AI Coach. If you as the guesser are a bit stuck on what guess to make next, you can use the AI coach to analyze the game state which includes difficulty, remaining attempts, and guess history. This AI coach acts as a layer added to the additional game logic which is an example of how AI can be integrated into the project.

4. Architecture Overview
   - Main components
   - Data flow summary
   - How AI coaching fits into the system

   There are three components: app.py which is the full UI layer, logic_utils.py which stores the logic of the game, and ai_utils.py which is the layer I added now. For the data, the first step is all the front end where the user types a guess, selects a difficulty, and determines wheter they want to use the AI layer or not. Next app.py looks at the input and send it to the logic in logic_utils.py which then determines if the guess was correct or determines a hint and updates the score. Then that information is sent back to the game which is displayed to the user.

   ```mermaid
   flowchart LR
     subgraph User and Inputs
       user[User] --> ui[Streamlit UI]
       ui --> input[Guess + Difficulty + AI toggle]
     end

     subgraph Application Logic
       app[app.py] --> logic[Game logic (logic_utils.py)]
       app -->|if AI enabled| ai[A.I. Coach (ai_utils.py)]
       ai --> gemini[Gemini API]
       logic --> outcome[Outcome + Hint + Score]
     end

     subgraph Output
       outcome --> ui[Streamlit UI]
       ai --> ui
       ui --> debug[Developer debug info]
     end

     subgraph Validation
       tests[Automated tests]
       manual[Human review / Setup]
       tests --> logic
       tests --> ai
       manual --> ui
       manual --> tests
     end

     input --> app
     app --> outcome
     gemini --> ai
     ui --> manual
   ```

5. Setup Instructions
   - Prerequisites
   - Install dependencies
   - Set environment variables
   - Run the app

   For prerequisites, you need Python 3.10+ and a Google Gemini API key (the free tier works but quickly maxes out of tries). 
   Install dependencies:
   pip install -r requirements.txt
   Set up enviornment variables:
   cp env.example .env
   Open .env and set:
   GEMINI_API_KEY=your_gemini_key_here
   GEMINI_MODEL=gemini-2.0-flash
   Run the app:
   python -m streamlit run app.py

   Note: if you didn't set up the key properly, the game still runs without the AI feature. 


6. Sample Interactions
   - Example 1: user guess and AI coach response
   - Example 2: different difficulty or feedback case
   - Example 3: AI disabled or game-over behavior

   An interaction with the user guessing 25 the first time in normal mode (range 1-50) would return something like the following from the AI coach:
   "You've used 1 of 8 attempts. Your guess of 25 eliminates the lower half — the number is somewhere between 26 and 50. Try 37 or 38 next to split the remaining range in half."

7. Design Decisions
   - Why this architecture was chosen
   - Trade-offs made
   - Why AI coaching was integrated in this way

   The architecture being split into three different layers allowed for more cleaner code and let me test it much easier. One of the trade-offs made was using a Gemini API key rather than paying for Claude or Open AI because it was cheaper but this made testing much harder because I would always run out of my quotas for the day. This also led me to create a lot of safeguards for my code with the AI. For example, if the code tries to call the Gemini API key and it doesn't work 2 times, then it stops and displays an error message that doesn't interupt the process of the game. AI coaching was integrated in a optional layer that doesn't control any aspect of the game because it's goal was to assist and not to play or interfere in the game any other way. 

8. Testing Summary
   - What was tested
   - What passed
   - Any known limitations or edge cases

   A lot of my test cases focused on the new AI extension rather than the old code because I knew that was working from the previous testing. The tests I wrote checked for cases such as missing API key handling, missing sdk, API responses, any possible errors and an option for not having the API key set up. A major limitation of this is the fact that it only works Gemini API keys and the tests only show that it works locally. Given more time an edge case I could have really focused on was handling different output from using the API key since that could be formatted a bit better.

9. Reflection
   - What you learned about AI and problem-solving
   - How this project demonstrates your skills
   - What you would improve next

   The API key was one of the hardest thing to work work because I kept running out of my quota and I didn't want to pay for an AI service. This project demonstrates my skills because I used AI with guardrails and safeguards to make sure it doesn't take over the whole point of the game but the only helps when the user chooses to enable the AI coach. To improve this project next I would definitely find a better and more reliable API key to work with because the Gemini API key gave me such a hard time. 
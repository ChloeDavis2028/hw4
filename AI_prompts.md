# AI Prompts Log — HW4: Campus Customs Shop + Chatbot

I call my vibe coder 'Chloe'; the website's chatbot is also named Chloe.

## Problem 1: Vibe coder prompts

**Prompt:**
> Lets build a Campus Customs website that is a real customer website with a helpful chatbox named Chloe.  A front end and a backend wil be built and the brain is the PydanticAI agent.  Back end: Python FastAPI and front end: React + Vite TypeScript.  I want my cusotmers to get a full fun but motivated aviation experience while they are using this webiste. They will fly on a C-130 to different products, create accounts with whiz wheels chat about the items with headsets, matching items will appear on the page with pilots helmets and oxyden masks, and all honest answers about how over priced or not items are will be in the form of an ATC radio call. All stock will come from a local database.

**Follow-up prompt (if needed):**
> 

**What was lacking after the first:**


## Problem 2: Analyze the database

**Prompt:**
> open and then describe to me the different rows and columns and what everything in this database represents; any common concepts, material, summaries to be made and any obvious differences to discuss?ensure i understand all the fields and correctly navigate the information and overall intent.  Make sure I also at a min understand catalogue, inventory, and users

**Follow-up prompt (if needed):**
> show me the database in pictorial form

**Follow-up prompt:**
> write the output/harness.md and explain in detail what it means and what you did?

**Follow-up prompt:**
> so what was missing was the harness file and a picture of the tables. Also ensure in the harness file that each table has allof its fields and why the fields matter to shop or ensure the chatbot understands the why so it can help customers. Continue to add to this harness file

**What was lacking after the first:**
What was missing was the harness file and a picture of the tables.


## Problem 3: Build the Campus Customs website

**Prompt:**
> now create a react + Vite + TypeScript front end for the Campus Customs. I need a nav bar at the top that links to the following main oages:  Home, Products, About Us, Log In, Create Account. make sure the wording is similar to wording from the Campus Customs-Style wording thru the yalebulldogblue.com hor Home and About Us but all the wording needs to be in my voice, none of the text can be replicated.  and make sure on the Producst page the images are shown from the catalogue using the image paths from the database with basic info given like a fun ame, a regular name, price and a shot description.  have the description be cheery and use super flowery language with a couple of aviator and combat terms thrown in for fun.

**Follow-up prompt (if needed):**
> in addition, each product should open to a single item page. make sure there is a large image on the left and a full product tdescription on the right with a summary of the product, best way to use the product, price, sizes available and sizes left. creat a pretty card with fun colors on the products page so then the shopper can get to that single item page. In the bottom right of the site there needs to be a chat area. no need to have the chatbox speak to an agent yet... a button of some sort will do. at this point

**Follow-up prompt:**
> we are not done problem 3, I need to share about needing the API to read the database ad the backend/main.py will be used solely for the products and images.

**Follow-up (chose from options after my Problem 1 vision prompt):**
> Theme the current site

**What was lacking after the first:**
for problem 3 i left out the single - item product page and the chat area in the bottom right.  which is odd since it is on my screen


## Problem 4: Create account and login

**Prompt:**
> Now it is time to create an account that starts off with a log-in flow process. separate the login by new pilot customers and returning pilots. the login in needs to be an email and password combo and new accoutns need to get saved directly into the users table. and explain to me how you will ensure hackers can not access the passowrds once you store them. And also put a schedule in for changing passwords that makes sense, possibly every.  There is a test user that the seed database has

**Follow-up prompt (if needed):**
> i will have to login as a user and check that a brand new account can be created:  never unhas the stored value, read the salt out of the stored string, middle pievce, and do not make a new one at login...does this make sense/ explain?

**Follow-up prompt:**
> confirm step by step and explain in detail how you got the entire new and returning login with passowrd/salt etc to work? are the salts working? explain the roundtables? give me a checklist up to this point to understand every stp on building this website from start to finish

**Follow-up prompt:**
> change the new user to Colonel Chloe

**Follow-up prompt:**
> email needs to change to chloe too

**Follow-up prompt:**
> add in more animation for users

**Follow-up prompt:**
> yes and create one more account called Ace

**Follow-up prompt:**
> I still want a checklist of all requirements for this HW to be drafted and updated throut so i have a running log on how to create websites like this in the future.

**What was lacking after the first:**
so for problem 4 I did not explicitly tell Chloe how a login should check a password or both the test user and the brand-new account have to work


## Problem 5: PydanticAI agent backend

**Prompt:**
> now it is time to build the chatbot as a PydanticAI agent behind FastAPI plugged into my chat widget.  the API App will be ut in the backend/main.py, the fil that runs with Uvicorn.  Keep the agent as these four files next to it : ultimately in the main.pu i need a chat route to start so a message from the webiste returns an answer from the agent.  make the answers appear in ATC radio call format

**Follow-up prompt (if needed):**
> voice basics are pilot and ATC radio calls and safety basics need to be added into the prompts. dont allow stolen cards to be used, put gates on over purchasing and hacker or stealing from the webiste. ensure these updates are in . then lets chat on how the front end talk to FASTAPI andhow the agent is loaded

**Follow-up prompt:**
> ensure the backend runs from the backend/... and explain what all of this means? why is this part confusing to understand?

**Follow-up prompt:**
> lets tighten that.  instead call it Yale Tower

**Follow-up prompt:**
> (screenshot of "Make sure the backend runs from the backend/ folder like this: uvicorn main:app --reload --port 8000") what does this mean/

**Follow-up prompt:**
> ok explain that in simpler terms?

**Follow-up prompt:**
> so is this what I have set up for this website?

**Follow-up prompt:**
> so how would I haev said that command in my own words?

**Follow-up prompt:**
> make sure my checklist gets updated with all of this info

**What was lacking after the first:**
For problem 5, I needed to make sure all the safety rules were covered.


## Problem 6: Tools: product info and stock

**Prompt:**
> now lets look at what agent tools see the real info from the campus_customs.db:  description of the product, price, and stock, by size when reqd. do not invent prices or quatities.

**Follow-up prompt (if needed):**
> the agent must call the tools for price and stock. and then add or update return types in the model.py. use the prompts/prompt.md to help. in the output/harness, list every tool and in detail explain why the model fields chosen for lookup results and why

**Follow-up prompt:**
> for product design, lets add a bulldog in various forms, stances wearing various types of pilot gear while showing the product.. helmets, radio sets, flight suits, etc

**Follow-up prompt:**
> make the bulldog look more real like Dan from yale

**Follow-up prompt:**
> take a real photo of Dan and change that accordingly

**Follow-up prompt:**
> (chose: Licensed photo + credit; approved downloading the CC BY-SA 4.0 Kingman photo) perfect, do it

**Follow-up prompt:**
> use only the photo not the animation

**Follow-up (chose from options):**
> Also as a badge

**Follow-up prompt:**
> make it sixze appropriate for the platform being used

**Follow-up prompt:**
> make sure all of this gets savedsince I am not done but going to bed

**What was lacking after the first:**
For problem 6, I needed to tell the agent it had to call the tools for price and stock, and also ask for the tool list and field explanations in the harness.


## Problem 7: Chat search that updates the page

**Prompt:**
> ok lets start up again but this time for question 7:  I am going to add a feature that responds to customers questions when theyask about products.  The agent needsto dynamically show the matching items as product cards wiht a few details, price, fun name, real name and a short video of a funny reel or gif that is free advertising the product and the the front ender puts it on a webiste

**Follow-up prompt (if needed):**
> (chose: Make our own reel from each product's photo)

**Follow-up prompt:**
> ok so problem 5 i need to make sure all safety rules are covered and what does that look like once my website is fully protected?  spelling needs to be accurat  problem 6 i need to tell the agent it had to call the tools for price and stock, and also ask for the tool list and field explanations in the harness.  answer with accurate spelling and then in detail explain to me exactly what this means  problem 7 i did tell you where the gif or funny reel should come from?  I really dont know where they would come from so explain that to me and go ahead and give me three different options to choose from, ore funnier ones please

**Follow-up (chose from three funnier reel options):**
> Cargo drop

**Follow-up prompt:**
> is the single item page behavior built in prob 3 still work? it still needs to be able to open the detail view with the large image and the extra info

**Follow-up prompt:**
> make sure my prompts/prompts.md and output/harness pages are updated. then confirm i have finished problem 7

**Follow-up prompt:**
> what am i missing to make this objective more entertaining for my customer and poduct?  and again, dont forget to update my checklist and update the document that flows withit so I can have a version of all of these steps in a simplified manner for viewing after the homework is completely finished

**Follow-up prompt:**
> finally what am I missing to make sure i met the intent of the professor and that I receive a 100

**What was lacking after the first:**
For problem 7, I didn't know where the GIF or funny reel would come from.


## Problem 8: Customer memory

**Prompt:**
> lets move on to question 8...  all chat history must be saved in the database in a tale that is easy to read and must be reloadede when they return for all of my shoppers.  the agent needs to know the who meaning who they are chatting with, name and emailand a fun call sign. makre sure the agent can recall in agent deps or a clear pattern and or tools the agent can call.  and as always put an aviation or fun flying twist to it

**Follow-up prompt (if needed):**
> page context needs to be allowed enough and coded by the agent so that if a shopper isor someone else is on a product page and asks specific questions about any product, the agent knows exactly what the shopper is alking about.  the agent needs to follow, be on the same age as the shopper and solve any questions onfor the shopper In addition, guests can still chat but history is only persisting for logged in users.  document in the output/harness.md and explain to me how you did it.  how you stored the chat history, what fields the customer sees by the agent and how the page context is passed.  while doing all of this, look for gaps that can help the shopper and correct the website, always look for similarity between shoppers and provide recommendation avery day on how to better provide for those shoppers, and always look for ways to enagge in a more entertaining manner to all the customers.  communicate with me regularly if especially if changes should happed right away. also look for deficiencies and ways to attract different types of customers

**What was lacking after the first:**
For problem 8, I needed to make sure the agent followed the shopper in the product pages and that guest chats are not saved, but logged-in users' chats are.


## Problem 9: Usability improvements

**Prompt:**
> lets improve how the core shop works and improve it: 2 front end and two agent/backend usability improvments. Give me five options to choose from both improvments. Ideas can be maaking the agent run faster or cheaper, making the site look better and easier to use

**Follow-up prompt (if needed):**
> write an output/usability.md for each of the imprvments and put what you added and why it helped a Campus Customs shopper.then make the improvments show in the running app

(Built the recommended set: F1 flight search and filters, F5 phone-friendly menu, B3 one-shot filter search tool, B5 typo-proof search.)

**Follow-up prompt:**
> do the recommendations

**Follow-up prompt:**
> what am I missing from these problems that i should add per problem?  fix "Handsome Dan" errors

**Follow-up prompt:**
> lets get a solid update about the website, agent and front and back end, and then an update on my required documents, and finally an update on the assignemtnfor a 100 next

**Follow-up prompt:**
> i do not take screen shots for most things anymore, help me mke better prompts and guide me thru a checklist so I do not miss any gaps or opportunities

**What was lacking after the first:**
For problem 9, I should have recognized my own improvements first, plus I needed to fix certain errors, like "Handsome Dan".


## Problem 10: Style the website

**Prompt:**
> now the fun part... add a creative design so the webiste feels like a real Campus Custom storefront but with a twist... an aviation twist for all at Yale and outside of Yale.  all the creative pieces: fnts, colors, hierachy, motion, product presentation, chat feel, avaition culture and experience

**Follow-up prompt (if needed):**
> be creative , inspiring especially for young aviators and women and innovative. then in the output/design.md:  write about what you changed and why it would keep customers around to buy.  keep this short and factual

**Follow-up prompt:**
> my follow up lacked inspiration advice. but definetly do it now

**Follow-up prompt:**
> save this stuff

**What was lacking after the first:**
For problem 10, my first prompt lacked inspiration advice.


## Problem 11: Site testing

**Prompt:**
> now i need to test the live site and document it in output/app_check.html.  make sure you can double click it to open include short and clear captions

**Follow-up prompt (if needed):**
> chat check the inventory level of an item and do an noest stock and price check from the database and have dynamic search result cards appear after a category question like hoodies. make it one of the usability features from problem 9

**Follow-up prompt:**
> Make the html easy to grade
easy check, screenshot. and have one or two sentences on what the screenshot proves. put screenshot iamge files: output/app_check_images/ and link them drom app_check.html with relateive paths to fields like inventory etc

**Follow-up prompt:**
> for problem 11;  a follow up question is what checks can be run to better suit a more dynamic aviation pleasant relatioship?

**Follow-up prompt:**
> Add all 6 relationship checks to app_check.html with screenshots and what-this-proves lines.

**Follow-up prompt:**
> i like those inputs, make those changes

**What was lacking after the first:**
My first prompt didn't say which checks to run or how to make them easy to grade, and it only tested whether the site worked, not whether Chloe built a pilot relationship with the shopper.


## Problem 12: Audit trail, safety, finish harness

**Prompt:**
> so le of agent loop activity; letts build an audit trail. lets call it output/audit_trail.json

**Follow-up prompt (if needed):**
> use it for time, tool name,short arduments and results and stop reasons.  lets add safety rules to the prompt page to include stoppingnhackers and ensuring nothing illegal on the web page is happening

**Follow-up prompt:**
> how does the system fully work? make sure that is covered in the output/harness.md.  include model fields and explain what they are and why in models.py, tools and abilities and why, safeetyy rules and why and any specs; loop limits, result caps, models, how to run front and back

**Follow-up prompt:**
> I had quite a few follow up questions for problem 12. use them, but also help me understand what other gaps i am missing

**Follow-up prompt:**
> Fix both now: move the audit trail code into the four agent files and fix the lint error, then retest.

**Follow-up prompt:**
> yes and also standardize capitalization across the website; needs to  appear moreacademic

**Follow-up prompt:**
> can you add a few photos of real life c130s airdropping cargo?

**Follow-up prompt:**
> Yes, download those 3 photos and add them to the About page with credits.

**What was lacking after the first:**
My first prompt only named the audit trail file; it didn't say what to record (time, tool name, short arguments and results, stop reasons), and it left out the safety rules for stopping hackers and anything illegal, plus the full harness explanation of model fields, tools, safety rules and specs.


## Problem 13: Push to GitHub and submit the URL

**Prompt:**
> lets get ready to submit,  by dropping my code into hw4 folder and push it to a public GitHub.  then on Canvas, submit the repo URL.  make sure the real .env, campus_customs.db or product images in the GitHub repo are not put. use .gitignore and include the .env.example with placeholders only

**Follow-up prompt (if needed):**
> 

**What was lacking after the first:**


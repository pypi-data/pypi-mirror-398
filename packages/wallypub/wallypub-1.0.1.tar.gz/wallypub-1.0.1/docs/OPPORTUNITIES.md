# Contribution Opportunities

With this at a version 1.0.0, I wanted to capture a few thoughts about possible contributions some of them are refactors and some of them
are and where this could end up going with future iterations. People reading this guide are welcome to reach out with questions, implement these, and make a merge
request.

### Creating a Digest
A full guide on creating a digest would be fun. Creating a digest isn't a heavy lift, but sometimes documentation 
beyond a terminal man page is a boon for the weary soul. 

### Documentation 
I'm sure there are typos or examples that could be more clear. Feedback welcome.

### Settings Variable
The global `app_config` acts a singleton where all the settings are held. It's created at
run time and can be updated. Those values then get saved on updates. I would like to refactor
this to only pass the config elements we need into the functions rather than having this global with
a bunch of settings passed around. It was an expedient pattern for getting the settings out of a mix of
environment variables and JSON files but were I designing this from scratch, I would have prioritized doing more of a
dependency injection pattern. A refactor where the settings are initialized on run and then passed into the proper functions would be welcome.

### update_config.py
update_config.py is ripe for a refactor that abstracts how the configuration updates are made. This ended up in this state simply
because I added some time constraints to my own time for this application. 

### Default Cover Size

The default size is 1.6:1 or 8:5 aspect ratio, assuming it's vertical.
This size was chosen because browsing online indicated that it would be a solid default
for e-readers and tablets. Development of these epubs largely targeted a Kobo Libra 2.

The cover size isn't currently configurable but that is something I would be willing to move into the settings.

### HTML Parsing
I have noticed that there are some inconsistencies with the parsed articles. Often around
code related articles but sometimes not. Wallypub sometimes drops articles and I have not dug into
why yet, I have been trying to capture a wider swath of examples.

### Bash best practices
There are sections of the code that rely on executing bash commands through Python.
I would love to revisit these to make sure that it is done by adhering to best practices.
The processes were discovered by testing and performing them on my devices rather than deep reading
of the best bash ways. 

### Back Matter Adjustments
While I intentionally made it so that the back matter could be disabled, 
folks might want to add something of their own to every digest they create. 

Additionally, I would prefer that the images need not be another request to the web
but it was the solution I could get working with pypub quickly.

### Avoiding File Collisions 
The `avoid_file_collisions` function could use some love. I got it to a point where the functionality worked 
but it never felt elegant.

### Naming 
When this was a part of another project, `articles` were the way to think of individual items in the read it later 
service, Wallabag uses entries. Refactoring across the repo to make the naming more consistent would be a boon. 

### Tests
More and better tests are welcome. 

The generate_test.py file could use some work. It never got properly hit after a refactor. 

### Project/Build Setup
wallypub was my first endeavor at doing builds in Python. I do not like that I landed on the repo being named `wallypub`
and then within that there is  `src/wallypub`. It feels redundant and I'm not sure if that redundancy is inexperience or necessity. 
Advice and MRs on the structure & build is welcome. 

### Reusable Files 
Currently, two images are pulled from the web for the back matter page. This increases the calls wallypub makes. 
While users can disable this entirely, it would seem kinder to people's networks if these images were simply bundled into the package.

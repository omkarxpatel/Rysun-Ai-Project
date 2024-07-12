![alt text](../images/rysun_logo.png) 
<!-- <img src="https://www.rysun.com/wp-content/uploads/2023/07/rysun-logo-2.png" alt="Rysun" width="100"> -->
### Omkar Patel
##### Estimated Timeline: 6/27/2024 - 6/30/2024
## Rewrite the System to be Modular

### Objective:
Design a system that uses a consistent layout to generate various types of responses. For example, the same backend should support generating emails based on inputs and generating code snippets.

### Outline:
The project will be organized into multiple subfolders for different tasks, such as email generation and code generation.

```
src
    ├── main.py         // Main runner for everything, runs functions in server and loads HTML
    ├── server.py       // Server with backend functions
screens
    ├── email
       ├── index.html
       ├── config.py
    ├── coding
       ├── index.html
       ├── config.py

... // Other outlines & folders
requirements.txt
.env
.gitignore
```

### Tasks:
1. **Modularize Backend:**
   - Split `server.py` into multiple files: `main.py` and `server.py`.

2. **Create Task-Specific Folders:**
   - Establish folders for specific tasks, such as an `email` folder for the current `index.html` and `constants.py`.

3. **Develop a Backbone Template:**
   - Create a template structure that can be used for other designs and functionalities.

4. **Implement Universal Backend Functions:**
   - Ensure backend functions are designed in a way that any system (email generation, code generation, etc.) can call them.

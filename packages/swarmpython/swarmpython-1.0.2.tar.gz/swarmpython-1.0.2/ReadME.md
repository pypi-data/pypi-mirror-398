# 🐝 Swarm Intelligence Framework (V1)

**Swarm** is a lightweight Python framework designed to orchestrate multiple independent AI agents (or simple scripts) to solve a single problem. It uses **Swarm Intelligence** principles to aggregate the results of these agents, reducing error and increasing confidence.

We belive in swarm principle so we thought to make it easier for people to use.
Train lot of small model and combine the results rather than buildind a large model.

## 🚀 Key Features

* **Parallel Execution:** Runs all agents simultaneously using a high-performance thread pool.
* **Agnostic Loader:** Can load *any* Python script as an agent dynamically.
* **Auto-Strategy:** Automatically detects if your agents are returning numbers (Regression) or text/classes (Classification) and applies the correct math.
* **Deep Analytics:** Returns not just the answer, but the *confidence*, *entropy* (confusion), and *outlier data*. (this is expandable)

---

## 🛠️ Usage Guide
 **I.Setup:** Your script should have a function which executes the model and returns the output, then all set.
 **II.Execution:** 
 1.if the name of the fuction in the script is `predict` or `run`, then all good just pass the script's path, 

   ```python
   b1 = "model_1/pred.py"
   ```
    but is anyother name, then you have to pass the function name also and wrap it up in parenthesis,

   ```python
   b2 = ( "model_h52/pred.py", "dano")
   ```
 2.After that initialize the object like,
   ```python
   swarm = Swarm(b1, b2)
   ```
 3.Once initialized just call the run function,
 
   ```python
   results = swarm.run(input, priorities=[0.6, 0.1, 0.1,0.1,0.1], mode="numeric", sensitivity=1.5)
   ```
    -priorities, sensitivity and mode are all optional.
    -mode is automatically detected if doesn't specified.
    -if sensitivity value is lower then the outlier filtering will be strict, default value is 1.5.

- there are some sample codes for you,go tp our github repo( https://github.com/Feininon/swarmpython ) and just run main.py.
- feel free to contribute, we appreciate that.`

 

 
 









# Backtick - Programming Language
# By splot.dev

import re
import random
import requests
import time

class Backtick:
    def tokenize(self, code):
        
        # This will turn the code into a Python object for easier running.
        
        if not isinstance(code, str):
            return ("Code input must be string.", False)

        code_no_comments = re.sub("#.*$", "", code,flags=re.MULTILINE)
        code_newline_replaced = code_no_comments.replace("\n", ";;")
        code_split = code_newline_replaced.split(";;")

        tokens = []
        line = 0
        
        for command in code_split:
            if command:
                command_name = ""
                command_args = []
                count = 0
                escaped = False
                for char in command:
                    if escaped:
                        if not command_args == []:
                            command_args[-1]["value"] = command_args[-1]["value"] + char
                        else:
                            command_name = command_name + char
                        escaped = False
                    else:
                        if char == "|":
                            escaped = True
                        else:
                            if count == 0 and (char in ["\\", "<", ">"]):
                                return (f"Command {line+1}, character {count+1}: first character must be command.", False)
                            elif char in ["\\", "<", ">"]:
                                command_args.append({"type": char, "value":""})
                            elif not command_args == []:
                                command_args[-1]["value"] = command_args[-1]["value"] + char
                            else:
                                command_name = command_name + char
                            
                    count += 1
                tokens.append({"name": command_name, "arguments": command_args})
            else:
                tokens.append({}) 
            line += 1
        return (tokens, True)
    def run(self, tokens):

        # This will run this tokens.
        
        if not isinstance(tokens, list):
            return ("Tokens must be list.", False)

        jumpareas = {}

        line = 0
        for token in tokens:
            if token == {}:
                line+=1
                continue
            
            if token["name"] == "~":
                if not len(token["arguments"]) == 1:
                    return (f"Command {line+1}: invalid argument amount, must have 1.", False)
                if not token["arguments"][0]["type"] == ">":
                    return (f"Command {line+1}: must be string.", False)                    
                    
                jumpareas[token["arguments"][0]["value"]]=line
            line += 1

        variables = {"`j": 0.0, "`l": 1.0, "n":0.0, "s": ""}
        
        line = 0
        token = tokens[line]
        loop = False
        loopline = None
        loopend = None
        while True:
            if line >= len(tokens):
                break
            token = tokens[line]

            if token == {}:
                line += 1
                continue
            if token["name"] == "~":
                line += 1
                continue
            elif token["name"] == "+":
                value_one = None
                value_two = None
                if not len(token["arguments"]) == 3:
                    return (f"Command {line+1}: invalid argument amount, must have 3.", False)
                if not token["arguments"][0]["type"] == "\\":
                    return (f"Command {line+1}: argument 1 must be variable.", False)
                if (token["arguments"][1]["type"] == ">" and token["arguments"][2]["type"] == "<") or (token["arguments"][1]["type"] == "<" and token["arguments"][2]["type"] == ">"):
                    return (f"Command {line+1}: argument 2 and 3 must be strings and strings, integers and variables, numbers and numbers or variables and variables.", False)                    
                if not token["arguments"][0]["value"] in variables:
                    return (f"Command {line+1}: argument 1 does not exist as a variable.", False)
                if token["arguments"][1]["type"] == "\\":
                    if not token["arguments"][1]["value"] in variables:
                        return (f"Command {line+1}: argument 2 does not exist as a variable.", False)
                    else:
                        value_one = variables[token["arguments"][1]["value"]]
                else:
                    value_one = token["arguments"][1]["value"]
                if token["arguments"][2]["type"] == "\\":
                    if not token["arguments"][2]["value"] in variables:
                        return (f"Command {line+1}: argument 3 does not exist as a variable.", False)
                    else:
                        value_two = variables[token["arguments"][2]["value"]]
                else:
                    value_two = token["arguments"][2]["value"]
                    
                if token["arguments"][1]["type"] == "<":
                    value_one = float(value_one)
                if token["arguments"][2]["type"] == "<":
                    value_two = float(value_two)

                if not ((isinstance(value_one, float) and isinstance(value_two, float)) or (isinstance(value_one, str) and isinstance(value_two, str))):
                    return (f"Command {line+1}: Invalid type matching.", False)
                
                variables[token["arguments"][0]["value"]] = value_one + value_two
            elif token["name"] == "-":
                value_one = None
                value_two = None
                if not len(token["arguments"]) == 3:
                    return (f"Command {line+1}: invalid argument amount, must have 3.", False)
                if not token["arguments"][0]["type"] == "\\":
                    return (f"Command {line+1}: argument 1 must be variable.", False)
                if (token["arguments"][1]["type"] == ">" and token["arguments"][2]["type"] == ">") or (token["arguments"][1]["type"] == ">" and token["arguments"][2]["type"] == "<") or (token["arguments"][1]["type"] == "<" and token["arguments"][2]["type"] == ">"):
                    return (f"Command {line+1}: argument 2 and 3 must be, integers and variables, numbers and numbers or variables and variables.", False)                    
                if not token["arguments"][0]["value"] in variables:
                    return (f"Command {line+1}: argument 1 does not exist as a variable.", False)
                if token["arguments"][1]["type"] == "\\":
                    if not token["arguments"][1]["value"] in variables:
                        return (f"Command {line+1}: argument 2 does not exist as a variable.", False)
                    else:
                        value_one = variables[token["arguments"][1]["value"]]
                else:
                    value_one = token["arguments"][1]["value"]
                if token["arguments"][2]["type"] == "\\":
                    if not token["arguments"][2]["value"] in variables:
                        return (f"Command {line+1}: argument 3 does not exist as a variable.", False)
                    else:
                        value_two = variables[token["arguments"][2]["value"]]
                else:
                    value_two = token["arguments"][2]["value"]
                    
                if token["arguments"][1]["type"] == "<":
                    value_one = float(value_one)
                if token["arguments"][2]["type"] == "<":
                    value_two = float(value_two)

                if not ((isinstance(value_one, float) and isinstance(value_two, float))):
                    return (f"Command {line+1}: Invalid type matching.", False)
                
                variables[token["arguments"][0]["value"]] = value_one - value_two
            elif token["name"] == "*":
                value_one = None
                value_two = None
                if not len(token["arguments"]) == 3:
                    return (f"Command {line+1}: invalid argument amount, must have 3.", False)
                if not token["arguments"][0]["type"] == "\\":
                    return (f"Command {line+1}: argument 1 must be variable.", False)
                if (token["arguments"][1]["type"] == ">" and token["arguments"][2]["type"] == ">") or (token["arguments"][1]["type"] == ">" and token["arguments"][2]["type"] == "<") or (token["arguments"][1]["type"] == "<" and token["arguments"][2]["type"] == ">"):
                    return (f"Command {line+1}: argument 2 and 3 must be, integers and variables, numbers and numbers or variables and variables.", False)                    
                if not token["arguments"][0]["value"] in variables:
                    return (f"Command {line+1}: argument 1 does not exist as a variable.", False)
                if token["arguments"][1]["type"] == "\\":
                    if not token["arguments"][1]["value"] in variables:
                        return (f"Command {line+1}: argument 2 does not exist as a variable.", False)
                    else:
                        value_one = variables[token["arguments"][1]["value"]]
                else:
                    value_one = token["arguments"][1]["value"]
                if token["arguments"][2]["type"] == "\\":
                    if not token["arguments"][2]["value"] in variables:
                        return (f"Command {line+1}: argument 3 does not exist as a variable.", False)
                    else:
                        value_two = variables[token["arguments"][2]["value"]]
                else:
                    value_two = token["arguments"][2]["value"]
                    
                if token["arguments"][1]["type"] == "<":
                    value_one = float(value_one)
                if token["arguments"][2]["type"] == "<":
                    value_two = float(value_two)

                if not ((isinstance(value_one, float) and isinstance(value_two, float))):
                    return (f"Command {line+1}: Invalid type matching.", False)
                
                variables[token["arguments"][0]["value"]] = value_one * value_two
                
            elif token["name"] == "/":
                value_one = None
                value_two = None
                if not len(token["arguments"]) == 3:
                    return (f"Command {line+1}: invalid argument amount, must have 3.", False)
                if not token["arguments"][0]["type"] == "\\":
                    return (f"Command {line+1}: argument 1 must be variable.", False)
                if (token["arguments"][1]["type"] == ">" and token["arguments"][2]["type"] == ">") or (token["arguments"][1]["type"] == ">" and token["arguments"][2]["type"] == "<") or (token["arguments"][1]["type"] == "<" and token["arguments"][2]["type"] == ">"):
                    return (f"Command {line+1}: argument 2 and 3 must be, integers and variables, numbers and numbers or variables and variables.", False)                    
                if not token["arguments"][0]["value"] in variables:
                    return (f"Command {line+1}: argument 1 does not exist as a variable.", False)
                if token["arguments"][1]["type"] == "\\":
                    if not token["arguments"][1]["value"] in variables:
                        return (f"Command {line+1}: argument 2 does not exist as a variable.", False)
                    else:
                        value_one = variables[token["arguments"][1]["value"]]
                else:
                    value_one = token["arguments"][1]["value"]
                if token["arguments"][2]["type"] == "\\":
                    if not token["arguments"][2]["value"] in variables:
                        return (f"Command {line+1}: argument 3 does not exist as a variable.", False)
                    else:
                        value_two = variables[token["arguments"][2]["value"]]
                else:
                    value_two = token["arguments"][2]["value"]
                    
                if token["arguments"][1]["type"] == "<":
                    value_one = float(value_one)
                if token["arguments"][2]["type"] == "<":
                    value_two = float(value_two)

                if not ((isinstance(value_one, float) and isinstance(value_two, float))):
                    return (f"Command {line+1}: invalid type matching.", False)

                if value_two == 0.0:
                    return (f"Command {line+1}: cannot perform division by 0.", False)
                
                variables[token["arguments"][0]["value"]] = value_one / value_two
            elif token["name"] == "[":
                if loop:
                    return (f"Command {line+1}: already in loop, cannot nest loops.", False)
                if not len(token["arguments"]) == 0:
                    return (f"Command {line+1}: no arguments needed for loops.", False)
                
                if len(tokens) <= (line+1):
                    return (f"Command {line+1}: cannot have a loop starter at the last line.", False)
                
                loop = True
                loopline = line + 1
            elif token["name"] == "]":
                if not loop:
                    return (f"Command {line+1}: you are not in a loop, so you cannot end it.", False)
                if not len(token["arguments"]) == 0:
                    return (f"Command {line+1}: no arguments needed for loops.", False)
                loopend = line
                if variables["`l"] == 0:
                    loop = False
                    loopline = None
                    line = loopend
                    loopend = None
                else:
                    line = loopline
            elif token["name"] == ":":
                if loop:
                    return (f"Command {line+1}: you cannot jump while in a loop.", False)
                if not len(token["arguments"]) == 1:
                    return (f"Command {line+1}: you must have one argument.", False)
                if not token["arguments"][0]["type"] == ">":
                    return (f"Command {line+1}: argument 1 must be a string", False)

                if not (token["arguments"][0]["value"] in jumpareas):
                    return (f"Command {line+1}: missing jump area", False)
                
                if variables["`j"] == 0:
                    line = int(jumpareas[token["arguments"][0]["value"]])
                else:
                    pass
            elif token["name"] == "=":
                if not len(token["arguments"]) == 2:
                    return (f"Command {line+1}: you must have two arguments.", False)
                if not token["arguments"][0]["type"] == "\\":
                    return (f"Command {line+1}: argument 1 must be a variable", False)

                value = None
                if token["arguments"][1]["type"] == "\\":
                    value = variables[token["arguments"][1]["value"]]
                elif token["arguments"][1]["type"] == "<":
                    value = float(token["arguments"][1]["value"])
                elif token["arguments"][1]["type"] == ">":
                    value = token["arguments"][1]["value"]

                variables[token["arguments"][0]["value"]] = value
            elif token["name"] == "%":
                if not len(token["arguments"]) == 4:
                    return (f"Command {line+1}: you must have 4 arguments.", False)
                if not token["arguments"][0]["type"] == "\\":
                    return (f"Command {line+1}: argument 1 must be a variable", False)
                
                value = None
                if token["arguments"][1]["type"] == "\\":
                    value = variables[token["arguments"][1]["value"]]
                elif token["arguments"][1]["type"] == "<":
                    value = float(token["arguments"][1]["value"])
                elif token["arguments"][1]["type"] == ">":
                    value = token["arguments"][1]["value"]

                
                oneif = token["arguments"][2]["value"]
                if token["arguments"][2]["type"] == "\\":
                    oneif = variables[token["arguments"][2]["value"]]
                elif token["arguments"][2]["type"] == "<":
                    oneif = float(token["arguments"][2]["value"])
                elif token["arguments"][2]["type"] == ">":
                    oneif = token["arguments"][2]["value"]
                    
                twoif = token["arguments"][3]["value"]
                if token["arguments"][3]["type"] == "\\":
                    twoif = variables[token["arguments"][3]["value"]]
                elif token["arguments"][3]["type"] == "<":
                    twoif = float(token["arguments"][3]["value"])
                elif token["arguments"][3]["type"] == ">":
                    twoif = token["arguments"][3]["value"]

                if oneif == twoif:
                    variables[token["arguments"][0]["value"]] = value
            elif token["name"] == ",":
                if not len(token["arguments"]) == 4:
                    return (f"Command {line+1}: you must have 4 arguments.", False)
                if not token["arguments"][0]["type"] == "\\":
                    return (f"Command {line+1}: argument 1 must be a variable", False)
                
                value = None
                if token["arguments"][1]["type"] == "\\":
                    value = variables[token["arguments"][1]["value"]]
                elif token["arguments"][1]["type"] == "<":
                    value = float(token["arguments"][1]["value"])
                elif token["arguments"][1]["type"] == ">":
                    value = token["arguments"][1]["value"]

                
                oneif = token["arguments"][2]["value"]
                if token["arguments"][2]["type"] == "\\":
                    oneif = variables[token["arguments"][2]["value"]]
                elif token["arguments"][2]["type"] == "<":
                    oneif = float(token["arguments"][2]["value"])
                elif token["arguments"][2]["type"] == ">":
                    oneif = token["arguments"][2]["value"]
                    
                twoif = token["arguments"][3]["value"]
                if token["arguments"][3]["type"] == "\\":
                    twoif = variables[token["arguments"][3]["value"]]
                elif token["arguments"][3]["type"] == "<":
                    twoif = float(token["arguments"][3]["value"])
                elif token["arguments"][3]["type"] == ">":
                    twoif = token["arguments"][3]["value"]

                if oneif > twoif:
                    variables[token["arguments"][0]["value"]] = value
            elif token["name"] == ".":
                if not len(token["arguments"]) == 4:
                    return (f"Command {line+1}: you must have 4 arguments.", False)
                if not token["arguments"][0]["type"] == "\\":
                    return (f"Command {line+1}: argument 1 must be a variable", False)
                
                value = None
                if token["arguments"][1]["type"] == "\\":
                    value = variables[token["arguments"][1]["value"]]
                elif token["arguments"][1]["type"] == "<":
                    value = float(token["arguments"][1]["value"])
                elif token["arguments"][1]["type"] == ">":
                    value = token["arguments"][1]["value"]

                
                oneif = token["arguments"][2]["value"]
                if token["arguments"][2]["type"] == "\\":
                    oneif = variables[token["arguments"][2]["value"]]
                elif token["arguments"][2]["type"] == "<":
                    oneif = float(token["arguments"][2]["value"])
                elif token["arguments"][2]["type"] == ">":
                    oneif = token["arguments"][2]["value"]
                    
                twoif = token["arguments"][3]["value"]
                if token["arguments"][3]["type"] == "\\":
                    twoif = variables[token["arguments"][3]["value"]]
                elif token["arguments"][3]["type"] == "<":
                    twoif = float(token["arguments"][3]["value"])
                elif token["arguments"][3]["type"] == ">":
                    twoif = token["arguments"][3]["value"]

                if oneif < twoif:
                    variables[token["arguments"][0]["value"]] = value
            elif token["name"] == "!":
                if not len(token["arguments"]) == 1:
                    return (f"Command {line+1}: must have one argument.", False)
                one = token["arguments"][0]["value"]
                if token["arguments"][0]["type"] == "\\":
                    one = variables[token["arguments"][0]["value"]]
                elif token["arguments"][0]["type"] == "<":
                    one = float(token["arguments"][0]["value"])
                elif token["arguments"][0]["type"] == ">":
                    one = token["arguments"][0]["value"]

                print(one)
            elif token["name"] == "?":
                if not len(token["arguments"]) == 1:
                    return (f"Command {line+1}: must have one argument.", False)
                if not token["arguments"][0]["type"] == "\\":
                    return (f"Command {line+1}: first argument must be variable.", False)
                userinput = input(">> ")
                try:
                    variables[token["arguments"][0]["value"]] = int(userinput)
                except:
                    try:
                        variables[token["arguments"][0]["value"]] = float(userinput)
                    except:
                        variables[token["arguments"][0]["value"]] = userinput
            elif token["name"] == "^":
                if not len(token["arguments"]) == 3:
                    return (f"Command {line+1}: must have three arguments.", False)

                if not token["arguments"][0]["type"] == "\\":
                    return (f"Command {line+1}: argument one must be a variable", False)
                
                if not token["arguments"][1]["type"] == "\\":
                    return (f"Command {line+1}: argument two must be a variable", False)

                three = token["arguments"][2]["value"]
                if token["arguments"][2]["type"] == "\\":
                    three = variables[token["arguments"][2]["value"]]
                elif token["arguments"][2]["type"] == "<":
                    three = float(token["arguments"][2]["value"])
                elif token["arguments"][2]["type"] == ">":
                    return (f"Command {line+1}: argument three cannot be a string", False)
                
                if (int(three + 1) > len(variables[token["arguments"][1]["value"]])) or (int(three + 1) <= 0):
                    return (f"Command {line+1}: argument three must be a valid character number in argument two's variable", False)

                variables[token["arguments"][0]["value"]] = variables[token["arguments"][1]["value"]][three]
            elif token["name"] == "&":
                if not len(token["arguments"]) == 3:
                    return (f"Command {line+1}: must have three arguments.", False)

                if not token["arguments"][0]["type"] == "\\":
                    return (f"Command {line+1}: argument one must be a variable", False)

                two = token["arguments"][1]["type"]
                if token["arguments"][1]["type"] == "\\":
                    two = variables[token["arguments"][1]["value"]]
                elif token["arguments"][1]["type"] == "<":
                    try:
                        two = float(token["arguments"][1]["value"])
                    except:
                        return (f"Command {line+1}: argument two must be a integer", False)
                elif token["arguments"][1]["type"] == ">":
                    return (f"Command {line+1}: argument two cannot be a string", False)

                three = token["arguments"][2]["value"]
                if token["arguments"][2]["type"] == "\\":
                    three = variables[token["arguments"][2]["value"]]
                elif token["arguments"][2]["type"] == "<":
                    try:
                        three = int(token["arguments"][2]["value"])
                    except:
                        return (f"Command {line+1}: argument three must be a integer", False)
                elif token["arguments"][2]["type"] == ">":
                    return (f"Command {line+1}: argument three cannot be a string", False)

                if two >= three:
                    return (f"Command {line+1}: argument two cannot be larger or equal to argument three.", False)

                variables[token["arguments"][0]["value"]] = random.randint(two, three)
            elif token["name"] == "@":
                if not len(token["arguments"]) == 1:
                    return (f"Command {line+1}: must have one argument.", False)

                if not token["arguments"][0]["type"] == "\\":
                    return (f"Command {line+1}: argument one must be a variable", False)

                variables[token["arguments"][0]["value"]] = time.time()
            elif token["name"] == "_r":
                if not len(token["arguments"]) == 1:
                    return (f"Command {line+1}: must have one argument.", False)

                if not token["arguments"][0]["type"] == ">":
                    return (f"Command {line+1}: argument one must be a string", False)

                try:
                    with open(token["arguments"][0]["value"], 'r') as f:
                        content = f.read()
                    self.run(self.tokenize(str(content))[0])
                except Exception as e:
                    return (f"Command {line+1}: file reading and/or running failed: {e}", False)
            elif token["name"] == "_g":
                if not len(token["arguments"]) == 2:
                    return (f"Command {line+1}: must have two arguments.", False)

                if not token["arguments"][0]["type"] == "\\":
                    return (f"Command {line+1}: argument one must be a variable", False)

                if not token["arguments"][1]["type"] == ">":
                    return (f"Command {line+1}: argument two must be a string", False)
                
                try:
                    response = requests.get(token["arguments"][1]["value"], timeout = 10)
                except Exception as e:
                    return (f"Command {line+1}: GET request failed: {e}", False)

                variables[token["arguments"][0]["value"]] = response.text
            elif token["name"] == "_p":
                if not len(token["arguments"]) == 3:
                    return (f"Command {line+1}: must have three arguments.", False)
                    
                if not token["arguments"][0]["type"] == "\\":
                    return (f"Command {line+1}: argument one must be a variable", False)

                if not token["arguments"][1]["type"] == ">":
                    return (f"Command {line+1}: argument two must be a string", False)

                if not token["arguments"][2]["type"] == ">":
                    return (f"Command {line+1}: argument three must be a string", False)
                
                try:
                    response = requests.post(token["arguments"][1]["value"], data=token["arguments"][2]["value"], timeout=10)
                except Exception as e:
                    return (f"Command {line+1}: POST request failed: {e}", False)
                
                variables[token["arguments"][0]["value"]] = response.text
            else:
                return (f"Command {line+1}: invalid command.", False)
            line += 1
        
        return (True, True)
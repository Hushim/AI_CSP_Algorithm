import functools
import sys
from functools import reduce
from functools import partial
import queue
import re
import operator
import time

class ConstraintVar:
    # instantiation example: ConstraintVar( [1,2,3],'A1' )
    def __init__(self, d, n):
        self.domain = [v for v in d]
        self.name = n


class UnaryConstraint:
    # v1 is of class ConstraintVar
    # fn is the lambda expression for the constraint
    # instantiation example: UnaryConstraint( variables['A1'], functools.partial(unaryassign, n=3 ) )
    def __init__(self, v, fn):
        self.var = v
        self.func = fn


class BinaryConstraint:
    # v1 and v2 should be of class ConstraintVar
    # fn is the lambda expression for the constraint
    # instantiate example: BinaryConstraint( A1, A2, functools.partial(binsub, n=3 )
    # Use functools.partial to avoid loop problem of lambda
    def __init__(self, v1, v2, fn):
        self.var1 = v1
        self.var2 = v2
        self.func = fn


class TernaryConstraint:
    # v1, v2 and v3 should be of class ConstraintVar
    # fn is the lambda expression for the constraint
    # instantiate example: TernaryConstraint( A1, A2, A3 functools.partial(triadd, n=3 )
    # Use functools.partial to avoid loop problem of lambda
    def __init__(self, v1, v2, v3, fn):
        self.var1 = v1
        self.var2 = v2
        self.var3 = v3
        self.func = fn


def allDiff(constraints, v):
    # generate a list of constraints that implement the allDiff constraint for all variable combinations in v
    # constraints is a preconstructed list. v is a list of ConstraintVar instances.
    # call example: allDiff( constraints, [A1,A2,A3] ) will generate BinaryConstraint instances for [[A1,A2],[A2,A1],[A1,A3] ...
    fn = lambda x, y: x != y
    for i in range(len(v)):
        for j in range(len(v)):
            if (i != j):
                constraints.append(BinaryConstraint(v[i], v[j], fn))

"""To avoid loop problem of lambda, these functions are used to form constraints and should be used with functools.partial"""
def unaryassign(x, n):
    return x == n
def binadd(x, y, n):
    return x + y == n
def binsub(x, y, n):
    return abs(x - y) == n
def binmul(x, y, n):
    return x * y == n
def bindiv(x, y, n):
    return x / y == n or y / x == n
def triadd(x, y, z, n):
    return x+y+z == n
def trimul(x, y, z, n):
    return x * y * z == n

def setUpKenKen(variables, size, problem):
    # This setup is applicable to KenKen and Sudoku.
    # The VarNames list can then be used as an index or key into the dictionary, ex. variables['A1'] will return the ConstraintVar object

    rows = []
    cols = []
    domain = []

    # Set constraints
    uconstraints = []
    bconstraints = []
    tconstraints = []

    #generate variables
    for i in range(int(size)):
        rows.append(chr(ord('A') + i))
        cols.append(chr(ord('1') + i))
        domain.append(i + 1)
    varNames = [x + y for x in rows for y in cols]
    for var in varNames:
        variables[var] = ConstraintVar(domain, var)

    # establish the allDiff constraint for each column and each row

    # for example, for rows A,B,C, generate constraints A1!=A2!=A3, B1!=B2...   
    for r in rows:
        aRow = []
        for k in variables.keys():
            if (str(k).startswith(r)):
                # accumulate all ConstraintVars contained in row 'r'
                aRow.append(variables[k])
        # add the allDiff constraints among those row elements
        allDiff(bconstraints, aRow)

    # for example, for cols 1,2,3 (with keys A1,B1,C1 ...) generate A1!=B1!=C1, A2!=B2 ...
    for c in cols:
        aCol = []
        for k in variables.keys():
            key = str(k)
            # the column is indicated in the 2nd character of the key string
            if (key[1] == c):
                # accumulate all ConstraintVars contained in column 'c'
                aCol.append(variables[k])
        allDiff(bconstraints, aCol)

    #Add the constraints declared in the input file
    for p in problem:
        if len(p) == 2:
            uconstraints.append(UnaryConstraint(variables[p[1]], functools.partial(unaryassign, n=int(p[0]))))
        if len(p) - 2 == 2:
            if p[1] == "+":
                bconstraints.append(
                    BinaryConstraint(variables[p[2]], variables[p[3]], functools.partial(binadd, n=int(p[0]))))
                bconstraints.append(
                    BinaryConstraint(variables[p[3]], variables[p[2]], functools.partial(binadd, n=int(p[0]))))
            elif p[1] == "-":
                bconstraints.append(
                    BinaryConstraint(variables[p[2]], variables[p[3]], functools.partial(binsub, n=int(p[0]))))
                bconstraints.append(
                    BinaryConstraint(variables[p[3]], variables[p[2]], functools.partial(binsub, n=int(p[0]))))
            elif p[1] == "*":
                bconstraints.append(BinaryConstraint(variables[p[2]], variables[p[3]], functools.partial(binmul, n=int(p[0]))))
                bconstraints.append(BinaryConstraint(variables[p[3]], variables[p[2]], functools.partial(binmul, n=int(p[0]))))
            elif p[1] == "/":
                bconstraints.append(BinaryConstraint(variables[p[2]], variables[p[3]],
                                                    functools.partial(bindiv, n=int(p[0]))))
                bconstraints.append(BinaryConstraint(variables[p[3]], variables[p[2]],
                                                    functools.partial(bindiv, n=int(p[0]))))
        elif len(p) - 2 == 3:
            if p[1] == "+":
                tconstraints.append(TernaryConstraint(variables[p[2]], variables[p[3]], variables[p[4]],
                                                     functools.partial(triadd, n=int(p[0]))))
                tconstraints.append(TernaryConstraint(variables[p[3]], variables[p[2]], variables[p[4]],
                                                     functools.partial(triadd, n=int(p[0]))))
                tconstraints.append(TernaryConstraint(variables[p[4]], variables[p[2]], variables[p[3]],
                                                     functools.partial(triadd, n=int(p[0]))))
            elif p[1] == "*":
                tconstraints.append(TernaryConstraint(variables[p[2]], variables[p[3]], variables[p[4]],
                                                     functools.partial(trimul, n=int(p[0]))))
                tconstraints.append(TernaryConstraint(variables[p[3]], variables[p[2]], variables[p[4]],
                                                     functools.partial(trimul, n=int(p[0]))))
                tconstraints.append(TernaryConstraint(variables[p[4]], variables[p[2]], variables[p[3]],
                                                     functools.partial(trimul, n=int(p[0]))))

    return [uconstraints, bconstraints, tconstraints]

def Revise(bc):
    # The Revise() function from AC-3, which removes elements from var1 domain, if not arc consistent
    # A single BinaryConstraint or TernaryConstraint instance is passed in to this function.
    deleted = []
    if isinstance(bc, UnaryConstraint):
        dom = list(bc.var.domain)
        for x in dom:
            if not bc.func(x):
                bc.var.domain.remove(x)
        return True
    elif isinstance(bc, BinaryConstraint):
        dom1 = list(bc.var1.domain)
        dom2 = list(bc.var2.domain)

        # for each value in the domain of variable 1
        for x in dom1:
            needtoremove = True
            # >>>>
            # for each value in the domain of variable 2
            for y in dom2:
                # Since KenKen cannot have the same number in a row/column and there's only one constraint examined at a time,
                # add another constraint here to solve KenKen correctly
                if x == y:
                    continue
                # if nothing in domain of variable2 satisfies the constraint when variable1==x, remove x
                if True == bc.func(x, y):
                    needtoremove = False
                    break
            if needtoremove:
                deleted.append(x)
                bc.var1.domain.remove(x)
        return deleted

    elif isinstance(bc, TernaryConstraint):
        dom1 = list(bc.var1.domain)
        dom2 = list(bc.var2.domain)
        dom3 = list(bc.var3.domain)

        # for each value in the domain of variable 1
        for x in dom1:
            needtoremove = True
            bk = False

            # for each value in the domain of variable 2
            for y in dom2:
                # Since KenKen cannot have the same number in a row/column and there's only one constraint examined at a time,
                # add another constraint here to solve KenKen correctly
                if x == y and (bc.var1.name[0] == bc.var2.name[0] or bc.var1.name[1] == bc.var2.name[1]):
                    continue

                # for each value in the domain of variable 3
                for z in dom3:
                    # Since KenKen cannot have the same number in a row/column and there's only one constraint examined at a time,
                    # add another constraint here to solve KenKen correctly
                    if y == z and (bc.var2.name[0] == bc.var3.name[0] or bc.var2.name[1] == bc.var3.name[1]):
                        continue
                    if x == z and (bc.var1.name[0] == bc.var3.name[0] or bc.var1.name[1] == bc.var3.name[1]):
                        continue
                    # if nothing in domain of variable2 and variable3 satisfies the constraint when variable1==x, remove x
                    if True == bc.func(x, y, z):
                        needtoremove = False
                        bk = True
                        break
                if bk:
                    break
            if needtoremove:
                deleted.append(x)
                bc.var1.domain.remove(x)

        # Return the deleted elements for backtracking algorithm to restore the domain when the assignment is inconsistent
        return deleted


def nodeConsistent(uc):
    domain = list(uc.var.domain)
    for x in domain:
        if (False == uc.func(x)):
            uc.var.domain.remove(x)


def printDomains(vars, n):
    count = 0
    for k in sorted(vars.keys()):
        print(k, '{', vars[k].domain, '}, ', end="")
        count = count + 1
        if (0 == count % n):
            print(' ')

def printAssignment(assignment, n):
    if not assignment:
        print("Problem not consistent")
        return
    count = 0
    for k in sorted(assignment.keys()):
        print(k, '{', assignment[k], '}, ', end="")
        count += 1
        if 0 == count % n:
            print(' ')

def AC3(constraints):
    """
    AC3 main function
    """

    # Apply unary constraints first
    for u in constraints[0]:
        nodeConsistent(u)

    # Add all binary and ternary constraints into the queue
    worklist = queue.Queue()
    for i in constraints[1]:
        worklist.put(i)
    for i in constraints[2]:
        worklist.put(i)

    counter = 0

    while not worklist.empty():
        counter += 1
        constraint = worklist.get()
        deleted = Revise(constraint)
        if deleted:
            # Add all constraints affected by the revision to the queue
            for i in constraints[1]:
                if i.var2.name == constraint.var1.name:
                    worklist.put(i)
            for i in constraints[2]:
                if i.var2.name == constraint.var1 or i.var3.name == constraint.var1.name:
                    worklist.put(i)
    return counter

def backtracking(size, variables, constraints, MRVenabled):
    """
    Backtracking algorithm main function
    """

    # Apply unary constraints first
    for u in constraints[0]:
        nodeConsistent(u)

    counter = [0, 0, 0]

    # Call the recursive function
    result = backtrack({}, size, variables, constraints, MRVenabled, counter)

    # print statistics
    if MRVenabled:
        print("\nBacktracking with MRV finished, recursive function called for", counter[0], "times")
    else:
        print("\nBacktracking without MRV finished, recursive function called for", counter[0], "times")
    print("MAC inference checked", counter[1], "constraints")
    print("Restored", counter[2], "values in domains due to inconsistent inferences")
    return result


def backtrack(assignment, size, variables, constraints, MRVenabled, counter):

    """
    Backtracking algorithm recursive function
    """

    counter[0] += 1

    # Goal check
    if len(assignment) == size*size:
        return assignment

    # Select a variable to assign
    variable = selectVar(assignment, variables, MRVenabled)

    # Iterate through all possibility for this variable
    for value in variable.domain:
        assignment[variable.name] = value

        #MAC inference
        inferences = MAC(constraints, variable, value, counter)

        # If the assignment is legal
        if 'inconsistent' not in inferences.keys():
            result = backtrack(assignment, size, variables, constraints, MRVenabled, counter)
            if result:
                return result

        # Remove the assignment and inference
        assignment.pop(variable.name)
        if 'inconsistent' in inferences.keys():
            inferences.pop('inconsistent')
        for i in inferences.keys():
            # Add the removed values back to the domains
            counter[2] += len(inferences[i])
            variables[i].domain += inferences[i]
    return False

def MAC(constraints, variable, value, counter):
    """
    MAC function
    returns all values removed from each domain
    """
    inferences = {}
    red = []
    # Apply the assignment by removing all other vairables
    for i in variable.domain:
        if i != value:
            red.append(i)
    variable.domain = [value]
    inferences[variable.name] = red
    worklist = queue.Queue()

    # Add all influenced constraints into the queue
    for c in constraints[1]:
        if c.var2.name == variable.name:
            worklist.put(c)
    for c in constraints[2]:
        if c.var2.name == variable.name or c.var3.name == variable.name:
            worklist.put(c)

    # AC3
    while not worklist.empty():
        counter[1] += 1
        constraint = worklist.get()
        deleted = Revise(constraint)
        if deleted:
            for i in constraints[1]:
                if i.var2.name == constraint.var1.name:
                    worklist.put(i)
            for i in constraints[2]:
                if i.var2.name == constraint.var1 or i.var3.name == constraint.var1.name:
                    worklist.put(i)
            if constraint.var1.name not in inferences.keys():
                inferences[constraint.var1.name] = deleted
            else:
                inferences[constraint.var1.name] += deleted

            # If a domain is completely removed, this assignment is illegal
            if not constraint.var1.domain:
                inferences['inconsistent'] = True
                break
    return inferences


def selectVar(assignment, variables, MRVenabled):
    """
    Select a variable from the variables to assign value
    """
    if MRVenabled:
        # Choose the variable with least values in its domain
        least = None
        choice = 9999
        for i in variables.keys():
            if i not in assignment and len(variables[i].domain) < choice:
                least = variables[i]
                choice = len(variables[i].domain)
        return least
    else:
        # Choose first unassigned variable
        for i in variables.keys():
            if i not in assignment:
                return variables[i]

def main():
    # Read test cases from the file
    lines = open('testKenKen.txt').readlines()
    for l in lines:
        # Remove whitespace
        line = l.replace(" ", "")
        #Split by comma
        words = line.split(",")

        # Read puzzle size
        size = int(words.pop(0))
        constraintstr = []

        # Parse the constraints
        inside = False
        for w in words:
            if w[0] == '[':
                newcon = [w[1:]]
                inside = True
            elif inside:
                if w.endswith(']'):
                    newcon.append(w[:-1])
                    inside = False
                    constraintstr.append(newcon)
                else:
                    newcon.append(w)
        variables = dict()
        # Set up the variables and constraints
        cons = setUpKenKen(variables, size, constraintstr)
        t1 = time.clock()
        counter = AC3(cons)
        t2 = time.clock()
        print("\nAC3 finished, revised for", counter, "times")
        print("Time: %.4f seconds" % (t2 - t1))
        printDomains(variables, size)

        # Reset the variables and constraints
        variables = dict()
        cons = setUpKenKen(variables, size, constraintstr)
        MRVenabled = False
        t1 = time.clock()
        result = backtracking(size, variables, cons, MRVenabled)
        t2 = time.clock()

        print("Time: %.4f seconds" % (t2 - t1))
        printAssignment(result, size)

        MRVenabled = True
        # Reset the variables and constraints
        variables = dict()
        cons = setUpKenKen(variables, size, constraintstr)
        t1 = time.clock()
        result = backtracking(size, variables, cons, MRVenabled)
        t2 = time.clock()
        print("Time: %.4f seconds" % (t2 - t1))
        printAssignment(result, size)



if __name__ == '__main__':
    main()

import functools
import sys
from functools import reduce
from functools import partial
import queue
import re
import operator
import time


ops = {'+': operator.add,
       '-': operator.sub,
       '*': operator.mul,
       '/': operator.truediv,
       '==': operator.eq,
       '!=': operator.ne,
       '<': operator.lt,
       '<=': operator.le,
       '>': operator.gt,
       '>=': operator.ge,
       'abs': operator.abs,
       '^': operator.pow
       }
def foc(x, value):
    return x == value


class ConstraintVar:
    # instantiation example: ConstraintVar( [1,2,3],'A1' )
    # MISSING filling in neighbors to make it easy to determine what to add to queue when revise() modifies domain
    def __init__(self, d, n):
        self.domain = [v for v in d]
        self.name = n


class UnaryConstraint:
    # v1 is of class ConstraintVar
    # fn is the lambda expression for the constraint
    # instantiation example: UnaryConstraint( variables['A1'], lambda x: x <= 2 )
    def __init__(self, v, fn):
        self.var = v
        self.func = fn


class BinaryConstraint:
    # v1 and v2 should be of class ConstraintVar
    # fn is the lambda expression for the constraint
    # instantiate example: BinaryConstraint( A1, A2, lambda x,y: x != y )
    def __init__(self, v1, v2, fn):
        self.var1 = v1
        self.var2 = v2
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
def setFutoshiki(caseNum):


        #set UnaryConstraint and BinaryConstraint
        uconstraints = []
        bconstraints = []

        #open file
        lines = open('testFutoshiki.txt').readlines()
        # test this line in file
        testLine = caseNum 
        l = lines[testLine]
        l = re.sub('[ ]','',l)

        # size of puzzle is first number on the line
        n = eval(re.findall('^\d+',l)[0])
        l = re.sub('^\d+','',l)

        domain = []
        for i in range(n):
                domain.append(i+1)



        #initial variables
        rows = []
        cols = []
        variables = dict()
        for i in range (n):
                rows.append(chr(ord('A') + i))
                cols.append(chr(ord('1') + i))
        varNames = [ x+y for x in rows for y in cols ]

        for varname in varNames:
                variables[varname] = ConstraintVar( domain,varname )

        # find all "x Op y" 
        cs=re.findall('\w+\W+\w+',l)


        # for each, separate apart the variables, operator, and values
        for c in cs:
                # these are x < y OR x > y
                if re.findall('\w+\d+<\w+\d+',c) or re.findall('\w+\d+>\w+\d+',c):
                        lvar = re.findall('^\w+\d+',c)[0]
                        rvar = re.findall('\w+\d+$',c)[0]
                        op = re.findall('\W',c)[0]
                        #convert inequalities to lambda fn
                        if op == '>':
                            fn = lambda x,y: x > y
                            fn1 = lambda x,y: x < y
                        elif op == '<':
                            fn = lambda x,y: x < y
                            fn1 = lambda x,y: x > y
                        bconstraints.append(BinaryConstraint(variables[lvar], variables[rvar], fn))
                        bconstraints.append(BinaryConstraint(variables[rvar], variables[lvar], fn1))
                else:
                        # find x = value
                        if re.findall('\w+\d+=\d+',c):
                                var = re.findall('^\w+\d+',c)[0]
                                value = re.findall('\d+$',c)[0]
                        # find value = x
                        elif re.findall('\d+=\w+\d+',c):
                                var = re.findall('\w+\d+$',c)[0]
                                value = re.findall('^\d+$',c)[0]
                                # conver equalities to lambda fn
                        #fn = lambda x: x == eval(value)
                        fn = functools.partial(foc, value = int(value))
                        '''print("*****************var")
                        print(variables[var].name, value)
                        print('var,val,fn(1) ',var,'==',value,fn(1))'''
                        uconstraints.append(UnaryConstraint(variables[var], fn))


        # establish the allDiff constraint for each column and each row
        for r in rows:
            aRow = []
            for k in variables.keys():
                if (str(k).startswith(r)):
                    # accumulate all ConstraintVars contained in row 'r'
                    aRow.append(variables[k])
            # add the allDiff constraints among those row elements
            allDiff(bconstraints, aRow)

        for c in cols:
            aCol = []
            for k in variables.keys():
                key = str(k)
                # the column is indicated in the 2nd character of the key string
                if (key[1] == c):
                    # accumulate all ConstraintVars contained in column 'c'
                    aCol.append(variables[k])
            allDiff(bconstraints, aCol)
        return variables, n, uconstraints, bconstraints  

# --------------------------------------------------------------------------------------------
#########################            COMPLETE REVISE               ##########################

def Revise(bc):
    # The Revise() function from AC-3, which removes elements from var1 domain, if not arc consistent
    # A single BinaryConstraint instance is passed in to this function.
    # MISSING the part about returning sat to determine if constraints need to be added to the queue
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
                if x == y:
                    continue
                # >>>>>
                # if nothing in domain of variable2 satisfies the constraint when variable1==x, remove x
                # >>>>>
                if True == bc.func(x, y):
                    needtoremove = False
                    break
            if needtoremove:
                deleted.append(x)
                bc.var1.domain.remove(x)
        return deleted

# AC-3
def AC3(variables, constraints):

    for u in constraints[0]:
        nodeConsistent(u)

    worklist = queue.Queue()
    for i in constraints[1]:
        worklist.put(i)

    counter = 0

    while not worklist.empty():
        counter += 1
        constraint = worklist.get()
        deleted = Revise(constraint)
        if deleted:
            for i in constraints[1]:
                if i.var2.name == constraint.var1.name:
                    worklist.put(i)
                    
    return counter

def nodeConsistent(uc):
    domain = list(uc.var.domain)
    for x in domain:
        if not uc.func(x):
            uc.var.domain.remove(x)

def nodeConsistent(uc):
    domain = list(uc.var.domain)
    for x in domain:
        if not uc.func(x):
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

def backtracking(size, variables, constraints, MRVenabled):
    for u in constraints[0]:
        nodeConsistent(u)
    return backtrack({}, size, variables, constraints, MRVenabled)

#Backtracking
def backtrack(assignment, size, variables, constraints, MRVenabled):
    if len(assignment) == size*size:
        return assignment
    variable = selectVar(assignment, variables, MRVenabled)
    for value in variable.domain:
        assignment[variable.name] = value
        inferences = MAC(constraints, variables, variable, value)
        if 'inconsistent' not in inferences.keys():
            result = backtrack(assignment, size, variables, constraints, MRVenabled)
            if result:
                return result
        assignment.pop(variable.name)
        if 'inconsistent' in inferences.keys():
            inferences.pop('inconsistent')
        for i in inferences.keys():
            variables[i].domain += inferences[i]
    return False

#MAC
def MAC(constraints, variables, variable, value):
    inferences = {}
    red = []
    for i in variable.domain:
        if i != value:
            red.append(i)
    variable.domain = [value]
    inferences[variable.name] = red
    worklist = queue.Queue()
    consistent = True

    for c in constraints[1]:
        if c.var2.name == variable.name:
            worklist.put(c)
            
    while not worklist.empty():
        constraint = worklist.get()
        deleted = Revise(constraint)
        if deleted:
            for i in constraints[1]:
                if i.var2.name == constraint.var1.name:
                    worklist.put(i)
                    
            if constraint.var1.name not in inferences.keys():
                inferences[constraint.var1.name] = deleted
            else:
                inferences[constraint.var1.name] += deleted
            if not constraint.var1.domain:
                inferences['inconsistent'] = True
                consistent = False
                break
    return inferences

#Variable selecting
def selectVar(assignment, variables, MRVenabled):
    if MRVenabled:
        least = None
        choice = 9999
        for i in variables.keys():
            if i not in assignment and len(variables[i].domain) < choice:
                least = variables[i]
                choice = len(variables[i].domain)
        return least
    else:
        for i in variables.keys():
            if i not in assignment:
                return variables[i]
    
def tryFutoshiki(caseNum):

    print("******************test-case %d *************************"%(caseNum+1))
    variables, n , uconstraints, bconstraints = setFutoshiki(caseNum )
    cons = [uconstraints, bconstraints]
    counter = AC3(variables, cons)
    print("\nAC3 finished, executed for", counter, "times")
    printDomains(variables, n)
    print("***********************************************************")

    
    MRVenabled = False
    variables, n , uconstraints, bconstraints = setFutoshiki(caseNum )
    cons = [uconstraints, bconstraints]
    t1 = time.clock()
    result = backtracking(n, variables, cons, MRVenabled)
    t2 = time.clock()
    print("\nBacktracking without MRV finished")
    print("Time: %.4f seconds" % (t2 - t1))
    printAssignment(result, n)
    print("************************************************************")

    MRVenabled = True
    variables, n , uconstraints, bconstraints = setFutoshiki(caseNum )
    cons = [uconstraints, bconstraints]
    t1 = time.clock()
    result = backtracking(n, variables, cons, MRVenabled)
    t2 = time.clock()
    print("\nBacktracking with MRV finished")
    print("Time: %.4f seconds" % (t2 - t1))
    printAssignment(result, n)



if __name__ == '__main__':
    for i in range(4):
        tryFutoshiki(i)

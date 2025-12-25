def making_decision_tree():
    r_code = """
set.seed(123)
library(ISLR2)
library(tree)

# Data Preparation
# ----------------------
data(Carseats)

Sales.new = ifelse(Carseats$Sales >= 8, 'High', 'Low')
Sales.new = factor(Sales.new)

data = data.frame(Carseats, Sales.new)

ind = sample(1:nrow(data), size = 300)
train = data[ind, ]
test  = data[-ind, ]

# Fit Decision Tree

tree.fit = tree(Sales.new ~ . - Sales, data = train)
print(tree.fit)

plot(tree.fit)
text(tree.fit, pretty = 0)

summary(tree.fit)

# Test Set Prediction
# ----------------------
Sales.pred = predict(tree.fit, newdata = test, type = 'class')

conf.mat = table(Predicted = Sales.pred, Actual = test$Sales.new)
print(conf.mat)

test.error = mean(Sales.pred != test$Sales.new)
print(test.error)

# Cross-Validation
# ----------------------
optimal.tree = cv.tree(tree.fit, FUN = prune.misclass)
print(optimal.tree)

plot(optimal.tree$size, optimal.tree$dev, type = 'b')

# Pruned Tree
# ----------------------
best_size = optimal.tree$size[which.min(optimal.tree$dev)]

new.tree = prune.tree(tree.fit, best = best_size)
summary(new.tree)

plot(new.tree)
text(new.tree, pretty = 0)

Sales.pred.new = predict(new.tree, newdata = test, type = 'class')

conf.mat.new = table(Predicted = Sales.pred.new, Actual = test$Sales.new)
print(conf.mat.new)

test.error.new = mean(Sales.pred.new != test$Sales.new)
print(test.error.new)
"""
    return r_code

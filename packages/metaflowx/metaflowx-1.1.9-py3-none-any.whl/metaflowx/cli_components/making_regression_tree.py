def making_regression_tree():
    r_code = """
rm(list = ls())

# -------------------------
# Load Data
# -------------------------
library(MASS)
data(Boston)

dim(Boston)

# -------------------------
# Train–Test Split
# -------------------------
test  <- Boston[1:100, ]
train <- Boston[-c(1:100), ]

# -------------------------
# Fit Regression Tree
# -------------------------
library(tree)

tree_fit <- tree(medv ~ ., data = train)

plot(tree_fit)
text(tree_fit, pretty = 0)

tree_fit   # show splits

# -------------------------
# Training MSE
# -------------------------
yhat_train_tree <- predict(tree_fit, newdata = train)

train_MSE_tree <- mean((yhat_train_tree - train$medv)^2)
train_MSE_tree

# -------------------------
# Test MSE (Unpruned Tree)
# -------------------------
yhat_test_tree <- predict(tree_fit, newdata = test)

test_MSE_tree <- mean((yhat_test_tree - test$medv)^2)
test_MSE_tree

# -------------------------
# Cross-Validation for Optimal Tree Size
# -------------------------
optimal_tree <- cv.tree(tree_fit)
optimal_tree

plot(optimal_tree$size, optimal_tree$dev, type = 'b')

# -------------------------
# Prune the Tree
# -------------------------
new_tree <- prune.tree(tree_fit, best = 6)

plot(new_tree)
text(new_tree, pretty = 0)

# -------------------------
# Test MSE (Pruned Tree)
# -------------------------
yhat_new <- predict(new_tree, newdata = test)

test_MSE_new <- mean((test$medv - yhat_new)^2)
test_MSE_new
"""
    return r_code

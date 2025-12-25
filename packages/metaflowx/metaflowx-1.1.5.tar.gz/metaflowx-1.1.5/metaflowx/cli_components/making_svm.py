def making_svm():
    r_code = """
rm(list = ls())

# ============================================================
#              DATA PREPARATION
# ============================================================
library(ISLR)
data(Auto)

mpg.new <- as.factor(ifelse(Auto$mpg >= median(Auto$mpg), 1, -1))
data1 <- Auto[, -c(1, 9)]        # drop name + mpg
data  <- data.frame(mpg.new, data1)

n <- nrow(data)
set.seed(1234)
ind <- sample(1:n, size = 200, replace = FALSE)

train <- data[ind, ]
test  <- data[-ind, ]

library(e1071)

# ============================================================
#              LINEAR KERNEL SVM
# ============================================================
cat("\\n========== LINEAR KERNEL ==========\\n")

cost.grid <- c(0.001, 0.01, 0.1, 0.5, 1, 5, 10, 20, 100, 500)

tune.linear <- tune(
  svm,
  mpg.new ~ .,
  data = train,
  kernel = 'linear',
  ranges = list(cost = cost.grid)
)

best.linear <- tune.linear$best.model
summary(best.linear)

train.pred.lin <- predict(best.linear, newdata = train)
test.pred.lin  <- predict(best.linear, newdata = test)

train.err.lin <- mean(train.pred.lin != train$mpg.new)
test.err.lin  <- mean(test.pred.lin  != test$mpg.new)

# ============================================================
#              RADIAL KERNEL SVM
# ============================================================
cat("\\n========== RADIAL KERNEL ==========\\n")

cost.grid <- c(0.5, 1, 5, 10, 20, 50, 100, 500)
gamma.grid <- c(0.1, 0.5, 1, 5, 10)

tune.radial <- tune(
  svm,
  mpg.new ~ .,
  data = train,
  kernel = 'radial',
  ranges = list(cost = cost.grid, gamma = gamma.grid)
)

best.radial <- tune.radial$best.model
summary(best.radial)

train.pred.rad <- predict(best.radial, newdata = train)
test.pred.rad  <- predict(best.radial, newdata = test)

train.err.rad <- mean(train.pred.rad != train$mpg.new)
test.err.rad  <- mean(test.pred.rad  != test$mpg.new)

# ============================================================
#              POLYNOMIAL KERNEL SVM
# ============================================================
cat("\\n========== POLYNOMIAL KERNEL ==========\\n")

cost.grid <- c(0.5, 1, 10, 50, 100, 500, 1000)
degree.grid <- c(2, 3, 4, 5)

tune.poly <- tune(
  svm,
  mpg.new ~ .,
  data = train,
  kernel = 'polynomial',
  ranges = list(cost = cost.grid, degree = degree.grid)
)

best.poly <- tune.poly$best.model
summary(best.poly)

train.pred.poly <- predict(best.poly, newdata = train)
test.pred.poly  <- predict(best.poly, newdata = test)

train.err.poly <- mean(train.pred.poly != train$mpg.new)
test.err.poly  <- mean(test.pred.poly  != test$mpg.new)

# ============================================================
#              SUMMARY TABLE FOR ALL 3 MODELS
# ============================================================
model.name <- c('Linear SVM', 'Radial SVM', 'Polynomial SVM')
train.error <- c(train.err.lin, train.err.rad, train.err.poly)
test.error  <- c(test.err.lin,  test.err.rad,  test.err.poly)

cost <- c(best.linear$cost, best.radial$cost, best.poly$cost)
gamma <- c('-', best.radial$gamma, '-')
degree <- c('-', '-', best.poly$degree)

results <- data.frame(model.name, train.error, test.error, cost, gamma, degree)
results
"""
    return r_code

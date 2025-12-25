def generate_boosting():
    r_code = """
rm(list = ls())

# -----------------------------
# Load Data
# -----------------------------
library(ISLR2)
data(Hitters)

row.names(Hitters) <- NULL
data <- na.omit(Hitters)

# -----------------------------
# Log-transform Salary (response)
# -----------------------------
y <- log(data$Salary)

data1 <- data[ , -19]            # remove Salary column
data_new <- data.frame(data1, y) # add transformed y

# -----------------------------
# Train–Test Split
# -----------------------------
set.seed(123)
train <- data_new[1:180, ]
test  <- data_new[181:nrow(data_new), ]

# -----------------------------
# BOOSTING MODEL
# -----------------------------
library(gbm)

boost_tree <- gbm(
  y ~ .,
  data = train,
  distribution = 'gaussian',
  n.trees = 5000,
  shrinkage = 0.001,
  interaction.depth = 1
)

summary(boost_tree)  # variable importance

# -----------------------------
# Test MSE for shrinkage = 0.001
# -----------------------------
yhat_boost <- predict(boost_tree, newdata = test, n.trees = 5000)
MSE_boost <- mean((yhat_boost - test$y)^2)
MSE_boost

# -----------------------------
# SHRINKAGE GRID SEARCH
# -----------------------------
s <- c(0.001, 0.005, 0.008, 0.01, 0.05, 0.1, 0.2, 0.4, 0.5)
test.MSE <- array(dim = length(s))

for (i in 1:length(s)) {
  
  boost_tree <- gbm(
    y ~ .,
    data = train,
    distribution = 'gaussian',
    n.trees = 5000,
    shrinkage = s[i],
    interaction.depth = 1
  )
  
  yhat_boost <- predict(boost_tree, newdata = test, n.trees = 5000)
  test.MSE[i] <- mean((yhat_boost - test$y)^2)
}

table <- data.frame(shrinkage = s, Test_MSE = test.MSE)
table

# -----------------------------
# Plot shrinkage vs Test MSE
# -----------------------------
plot(s, test.MSE, type = 'b',
     xlab = 'Shrinkage (Learning Rate)',
     ylab = 'Test MSE',
     main = 'Boosting Shrinkage vs Test MSE')
"""
    return r_code

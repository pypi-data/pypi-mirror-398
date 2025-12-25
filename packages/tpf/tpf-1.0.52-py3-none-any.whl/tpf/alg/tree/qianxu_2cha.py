# 定义二叉树节点类  
class TreeNode:  
    def __init__(self, val=0, left=None, right=None):  
        self.val = val  
        self.left = left    # 左指针
        self.right = right  # 右指针
  
# 前序遍历函数（递归实现）  
def preorder_traversal_recursive(root):  
    if root is None:  
        return []  
    result = [root.val]  
    # 从这里开始递归，使用extend合并返回结果
    result.extend(preorder_traversal_recursive(root.left))  
    result.extend(preorder_traversal_recursive(root.right))  
    return result  
  
# 前序遍历函数（迭代实现）  
def preorder_traversal_iterative(root):  
    if root is None:  # init方法中初始化为None 
        return []  
      
    stack, result = [root], []  
      
    while stack:  
        node = stack.pop()  
        result.append(node.val)  
          
        # 先压右子节点，再压左子节点，因为栈是后进先出  
        if node.right:  
            stack.append(node.right)  
        if node.left:  
            stack.append(node.left)  
      
    return result  
  
# 示例用法  
if __name__ == "__main__":  
    # 创建一个示例二叉树  
    #       1  
    #      / \  
    #     2   3  
    #    / \  
    #   4   5  
    tree = TreeNode(1)  
    tree.left = TreeNode(2)  
    tree.right = TreeNode(3)  
    tree.left.left = TreeNode(4)  
    tree.left.right = TreeNode(5)  
      
    # 使用递归方法前序遍历  
    # print("Preorder Traversal (Recursive):", preorder_traversal_recursive(tree))  #Preorder Traversal (Recursive): [1, 2, 4, 5, 3]
      
    # 使用迭代方法前序遍历  
    print("Preorder Traversal (Iterative):", preorder_traversal_iterative(tree))  #Preorder Traversal (Recursive): [1, 2, 4, 5, 3]
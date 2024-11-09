<?php
$message = '';
$isSuccess = false;

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // 获取表单输入并进行安全处理
    $url = filter_input(INPUT_POST, 'newUrl', FILTER_SANITIZE_URL);
    $password = filter_input(INPUT_POST, 'password', FILTER_SANITIZE_STRING);

    // 设定正确的密码
    $correctPassword = "XXXXXXX"; // 替换为你的实际密码

    // 验证密码
    if ($password === $correctPassword) {
        // 验证 URL
        if (filter_var($url, FILTER_VALIDATE_URL)) {
            // 修改 index.html 文件中的内容
            $file_path = './index.html';

            // 检查文件是否可读取
            if (is_readable($file_path)) {
                $content = file_get_contents($file_path);

                // 假设你要替换 window.location.href
                $newContent = preg_replace('/window\.location\.href\s*=\s*["\'].*?["\']/', 'window.location.href = "' . $url . '"', $content);

                // 写回文件并检查写入是否成功
                if (file_put_contents($file_path, $newContent) !== false) {
                    $message = "更新成功！";
                    $isSuccess = true;
                } else {
                    $message = "写入文件失败，请检查文件权限。";
                }
            } else {
                $message = "无法读取文件，请检查文件路径。";
            }
        } else {
            $message = "无效的链接！";
        }
    } else {
        $message = "密码错误，无法修改链接。";
    }
} else {
    // 返回 405 错误
    header("HTTP/1.1 405 Method Not Allowed");
    $message = "不允许的请求方法。";
}
?>

<!DOCTYPE html>
<html lang="zh">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>操作结果</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f0f4f8; /* 更柔和的背景色 */
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            text-align: center;
            width: 90%;
            max-width: 400px;
        }
        h1 {
            color: #28a745; /* 绿色标题 */
            margin-bottom: 20px;
            font-size: 2em; /* 增大标题字体 */
        }
        p {
            font-size: 1.2em;
            color: #495057;
            margin-bottom: 20px;
        }
        .success {
            color: #28a745;
        }
        .error {
            color: red;
        }
        a {
            display: inline-block;
            margin-top: 20px;
            text-decoration: none;
            color: white;
            background: #28a745; /* 绿色按钮 */
            padding: 10px 20px;
            border-radius: 5px;
            transition: background 0.3s;
        }
        a:hover {
            background: #218838; /* 悬停时变暗 */
        }
    </style>
</head>
<body>
    <div class="container">
        <h1><?php echo $isSuccess ? '成功' : '错误'; ?></h1>
        <p class="<?php echo $isSuccess ? 'success' : 'error'; ?>">
            <?php echo htmlspecialchars($message); ?>
        </p>
        <a href="edit.html">返回表单</a> <!-- 替换为你的表单页面 -->
    </div>
</body>
</html>

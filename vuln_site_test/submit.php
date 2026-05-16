<?php
// intentionally naive form handler
$name = isset($_POST['name']) ? $_POST['name'] : '';
$email = isset($_POST['email']) ? $_POST['email'] : '';
?>
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Submit</title></head>
<body>
  <h1>Submitted</h1>
  <p>Name: <?php echo $name; ?></p>
  <p>Email: <?php echo $email; ?></p>
</body>
</html>
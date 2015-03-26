<?php

class Database {
	private $conn;

	public function connect($host, $username, $password, $db) {
		try {
			$this->conn = new PDO("mysql:host=$host;dbname=$db", $username, $password);
			$this->conn->exec("SET CHARACTER SET utf8");
		} catch (Exception $e) {
			echo $e->getMessage();
		}
	}

	public function execute($query, $params = array(), $style=PDO::FETCH_BOTH, $arg=null) {
		$statement = $this->conn->prepare($query);
		$success = $statement->execute($params);
		error_reporting(E_ALL);
		if ($success) {
			switch ($style) {
				case PDO::FETCH_BOTH:
					return $statement->fetchAll(PDO::FETCH_BOTH);
				case PDO::FETCH_CLASS:
					return $statement->fetchAll(PDO::FETCH_CLASS, $arg);
				case PDO::FETCH_ASSOC:
					return $statement->fetchAll(PDO::FETCH_ASSOC);
				case PDO::FETCH_COLUMN | PDO::FETCH_GROUP:
					return $statement->fetchAll(PDO::FETCH_COLUMN | PDO::FETCH_GROUP, $arg);
				case PDO::FETCH_COLUMN:
					return $statement->fetchAll(PDO::FETCH_COLUMN, $arg);
				case PDO::FETCH_GROUP:
					return $statement->fetchAll(PDO::FETCH_GROUP);
				case PDO::FETCH_FUNC:
					return $statement->fetchAll(PDO::FETCH_FUNC, $arg);
				default:
					return $statement->fetchAll($style);
			}
		} else {
			return false;
		}
	}
}
<?php

abstract class Route {
	protected $db;

	public function __construct() {
		$this->db = new Database();
		$creds = parse_ini_file('config.ini');
		$this->db->connect($creds['host'], $creds['user'], $creds['password'], $creds['database']);
	}

	public function sendJSON($data) {
		header('Content-Type: application/json');
		echo json_encode($data);
	}

	public function send404() {
		http_response_code(404);
	}
}

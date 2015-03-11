<?php

class Schools_One extends Route {

	public function get($var) {
		$school = urldecode($var);
		$schoolBySlug = $this->fetchBySlug($school);
		if (!is_null($schoolBySlug)) {
			return $this->sendJSON($schoolBySlug);
		}

		$schoolById = $this->fetchById($school);
		if (!is_null($schoolById)) {
			return $this->sendJSON($schoolById);
		} else {
			return $this->send404();
		}
	}

	private function fetchBySlug($slug) {
		$query = "SELECT id, name, slug FROM schools WHERE slug = :slug;";
		$result = $this->db->execute($query, array(":slug" => $slug), PDO::FETCH_CLASS, "School");

		if (count($result) > 0) {
			return $result[0];
		} else {
			return null;
		}
	}

	private function fetchById($id) {
		$query = "SELECT id, name, slug FROM schools WHERE id = :id;";
		$result = $this->db->execute($query, array(":id" => $id), PDO::FETCH_CLASS, "School");

		if (count($result) > 0) {
			return $result[0];
		} else {
			return null;
		}
	}
}
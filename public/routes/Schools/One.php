<?php

class Schools_One extends Route {

	public function get($slug) {
		$query = "SELECT id, name, slug FROM schools WHERE slug = :slug;";
		$result = $this->db->execute($query, array(":slug" => $slug), PDO::FETCH_CLASS, "School");

		if (count($result) > 0) {
			$this->sendJSON($result[0]);
		} else {
			$this->send404();
		}
	}
}
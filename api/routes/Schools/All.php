<?php

class Schools_All extends Route {

	public function get() {
		$query = "SELECT id, name, slug FROM schools;";
		$result = $this->db->execute($query, array(), PDO::FETCH_CLASS, "School");
		$this->sendJSON($result);
	}
}
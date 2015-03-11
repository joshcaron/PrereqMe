<?php

class Schools_Departments_One extends Route {

	public function get($school, $dept) {
		$query = "SELECT d.id, d.name, d.abbreviation FROM departments AS d"
		         . " JOIN schools AS s ON s.id = d.school_id"
		         . " WHERE s.slug = :school AND d.abbreviation = :dept;";
		$result = $this->db->execute($query,
		                             array(":school" => $school, ":dept" => $dept),
		                             PDO::FETCH_CLASS,
		                             "Department");
		if (count($result) > 0) {
			$this->sendJSON($result[0]);
		} else {
			$this->send404();
		}
	}
}
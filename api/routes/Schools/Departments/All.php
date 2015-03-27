<?php

class Schools_Departments_All extends Route {

	public function get($school) {
		$query = "SELECT d.id, d.name, d.abbreviation FROM departments AS d JOIN schools AS s ON s.id = d.school_id WHERE s.slug = :school;";
		$result = $this->db->execute($query, array(":school" => $school), PDO::FETCH_CLASS, "Department");
		$this->sendJSON($result);
	}
}
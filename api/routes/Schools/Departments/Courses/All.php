<?php

class Schools_Departments_Courses_All extends Route {

	public function get($school, $dept) {
		$query = "SELECT c.id, c.number, c.title, c.description, c.prereq_str FROM courses AS c"
		         . " JOIN departments AS d ON d.id = c.department_id"
		         . " JOIN schools AS s ON s.id = d.school_id"
		         . " WHERE s.slug = :school AND d.abbreviation = :dept;";
		$result = $this->db->execute($query,
		                             array(":school" => $school, ":dept" => $dept),
		                             PDO::FETCH_CLASS,
		                             "Course");

		$this->sendJSON($result);
	}
}
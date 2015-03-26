<?php

class Schools_Departments_Courses_One extends Route {
	
	public function get($school, $dept, $course) {
		$query = "SELECT c.id, d.abbreviation, c.number, c.title, c.description, c.prereq_str FROM courses AS c"
		         . " JOIN departments AS d ON d.id = c.department_id"
		         . " JOIN schools AS s ON s.id = d.school_id"
		         . " WHERE s.slug = :school AND d.abbreviation = :dept AND c.number = :course;";
		$result = $this->db->execute($query,
		                             array(":school" => $school, ":dept" => $dept, ":course" => $course),
		                             PDO::FETCH_CLASS,
		                             "Course");

		if (count($result) > 0) {
			$course = $result[0];
			$course->prereqs = $this->getPrereqs($course);
			$course->dependents = $this->getDependents($course);
			$this->sendJSON($course);
		} else {
			$this->send404();
		}
	}

	private function getDependents($course) {
		$query = "SELECT d.abbreviation, c.number, c.title, c.description FROM"
		         . " (SELECT p.course_id"
		              . " FROM prerequisites AS p"
		              . " JOIN courses AS c ON c.id = p.prereq_id"
		              . " JOIN departments AS d ON d.id = c.department_id"
		              . " WHERE c.id = :id) AS prereq"
		          . " JOIN courses AS c ON c.id = prereq.course_id"
		          . " JOIN departments AS d ON d.id = c.department_id;";
		return $this->db->execute($query, array(":id" => $course->id), PDO::FETCH_CLASS, "Course");

	}

	private function getPrereqs($course) {
		$query = "SELECT prereq_id, grouping FROM prerequisites WHERE course_id = :id;";
		$result = $this->db->execute($query,
		                             array(":id" => $course->id));
		$pre_ids = [];
		for ($i = 0; $i < count($result); $i++) {
			$prereq = $result[$i];
			$group = $prereq["grouping"];
			$id = $prereq["prereq_id"];
			if (!array_key_exists($group, $pre_ids)) {
				$pre_ids[$group] = [];
			}
			array_push($pre_ids[$group], $id);
		}

		$prereqs = [];
		for ($i = 0; $i < count($pre_ids); $i++) {
			$group = $pre_ids[$i];
			for ($p = 0; $p < count($group); $p++) {
				$id = $group[$p];
				$course = $this->getCourseById($id);
				$course->prereqs = $this->getPrereqs($course);
				if (!array_key_exists($i, $prereqs)) {
					$prereqs[$i] = [];
				}
				array_push($prereqs[$i], $course);
			}
		}
		return $prereqs;
	}

	private function getCourseById($id) {
		$query = "SELECT c.id, d.abbreviation, c.number, c.title, c.description, c.prereq_str FROM courses AS c "
		         . " JOIN departments AS d ON d.id = c.department_id"
		         . " WHERE c.id = :id;";
		$result = $this->db->execute($query,
		                             array(":id" => $id),
		                             PDO::FETCH_CLASS,
		                             "Course");
		return $result[0];

	}
}
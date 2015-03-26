<?php

class Status extends Route {
	public function get() {
		$this->sendJSON(array(
			"status" => "OK"
		));
	}
}

<?php

function lib_autoload($class) {
	@include_once(__DIR__ . '/lib/' . str_replace('_', '/', $class) . '.php');
}
spl_autoload_register('lib_autoload');

function routes_autoload($class) {
	@include_once(__DIR__ . '/routes/' . str_replace('_', '/', $class) . '.php');
}
spl_autoload_register('routes_autoload');

function obj_autoload($class) {
	@include_once(__DIR__ . '/obj/' . str_replace('_', '/', $class) . '.php');
}
spl_autoload_register('obj_autoload');
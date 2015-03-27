'use strict';

prereqApp.factory('DepartmentService', ['$http', '$cookies', '$q', 'config', function($http, $cookies, $q, config) {
	var department = {
		// Stored departments by school
		stored: {},

		'getDepartmentsForSchool': function(school) {
			var deffered = $q.defer();
			var DepartmentService = this;
			if (this.stored[school.slug] !== undefined) {
				console.log("Loaded departments from cache");
				deffered.resolve(this.stored[school.slug]);
			} else {
				this._getDepartmentList(school.slug)
					.then(function(response) {
						console.log("Got departments from API");
						DepartmentService.stored[school.slug] = response.data;
						deffered.resolve(response.data);
					}, function(error, status) {
						deffered.reject('Failed to get departments:' + status);
					});
			}
			return deffered.promise;
		},

		'getDepartment': function(school, department) {
			var deffered = $q.defer();

			if (this.stored[school.slug] !== undefined) {
				console.log("Loading department from cache.");
				var found = _.find(this.stored[school.slug], function(dept) {
					return dept.abbreviation == department;
				});
				if (found) {
					deffered.resolve(found);
				} else {
					deffered.reject("Bad cache.");
				}
			} else {
				this._getDepartmentByAbbv(school.slug, department)
					.then(function(response) {
						console.log("Got department from API");
						deffered.resolve(response.data);
					}, function(error) {
						deffered.reject('Failed to get department: ' + error.status);
					});
			}

			return deffered.promise;
		},

		'_getDepartmentList': function(slug) {
			console.log("Getting departments");
			return $http.get(config.API_URL + '/schools/' + slug + '/departments');
		},

		'_getDepartmentByAbbv': function(slug, abbv) {
			return $http.get(config.API_URL + '/schools/' + slug + '/departments/' + abbv);
		}

	};
	return department;
}]);

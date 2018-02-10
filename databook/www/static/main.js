(function () {

  'use strict';

  angular.module('DatabookApp', ['ui.bootstrap'])

     .controller('MasterController', ['$scope', '$log', '$http', '$uibModal',
        function($scope, $log, $http, $uibModal) {
          $scope.isNavCollapsed = true;
          $scope.menustatus = {
            is_tools_open: false
          };

          $scope.open = function(group_url) {
            window.open(group_url, '_self')
          };
      }
    ])

    .controller('SearchController', ['$scope', '$log', '$http',
      function($scope, $log, $http) {

        $scope.formData = {"searchTerm": "", "nodeType": "person", "csrf_token": 'nil'};

        $scope.columns = [];
        $scope.tabledata = [];
        $scope.isShow = 0;

        $scope.getResults = function() {
          $http.post('/search', JSON.stringify($scope.formData)).
            then(function successCallback(response) {
                var results = response.data;
                if ($scope.formData.nodeType == "person") {
                    $scope.columns = ['name','email','id'];
                    $scope.tabledata = results;
                    $scope.isShow = 1;
                }
                if ($scope.formData.nodeType == "group") {
                    $scope.columns = ['name'];
                    $scope.tabledata = results;
                    $scope.isShow = 1;
                }
                if ($scope.formData.nodeType == "tableau") {
                    $scope.columns = ['name'];
                    $scope.tabledata = results;
                    $scope.isShow = 1;
                }
                if ($scope.formData.nodeType == "table") {
                    $scope.columns = ['name'];
                    $scope.tabledata = results;
                    $scope.isShow = 1;
                }
            },
            function errorCallback(error) {
                $log.log(error);
            });
        };
    }
  ])
   .controller('PersonController', ['$scope', '$log', '$http',
      function($scope, $log, $http) {

    }
  ])
   .controller('GroupController', ['$scope', '$log', '$http', '$window',
      function($scope, $log, $http, $window) {
        $scope.isFavorite = false;
        $scope.isEditing = false;
        $scope.formData = {"groupTitle": '', "group_uuid": '', "groupLink": '', "linkDesc": ''};

        $scope.setGroup = function(group_uuid, group_name, group_link, link_desc) {
          $scope.formData['group_uuid'] = group_uuid;
          $scope.formData['groupTitle'] = group_name;
          $scope.formData['groupLink'] = group_link;
          $scope.formData['linkDesc'] = link_desc;
          if ($scope.formData['group_uuid'] == '-1') {
            $scope.isEditing = true;
          }
        }

        $scope.favorite = function() {
          $scope.isFavorite = !$scope.isFavorite;

          $http.post('/favorite_group', {"favorite": $scope.isFavorite, "group_uuid": $scope.formData['group_uuid']}).
            then(function successCallback(response) {
            },
            function errorCallback(error) {
                $log.log(error);
            });
        }

        $scope.createGroup = function() {
          $http.post('/create_group', $scope.formData).
            then(function successCallback(response) {
              var results = response.data;
              window.open(results['url'], '_self');
            },
            function errorCallback(error) {
                $log.log(error);
                $window.alert(error.data['error']);
            });
        }

        $scope.leaveGroup = function(groupUuid) {
          $log.log(groupUuid);
          $http.post('/leave_group', {"uuid": groupUuid}).
            then(function successCallback(response) {
              var results = response.data;
              window.open(results['url'], '_self');
            },
            function errorCallback(error) {
                $log.log(error);
                $window.alert(error.data['error']);
            }); 
        }

        $scope.joinGroup = function(groupUuid) {
          $log.log(groupUuid);
          $http.post('/join_group', {"uuid": groupUuid}).
            then(function successCallback(response) {
              var results = response.data;
              window.open(results['url'], '_self');
            },
            function errorCallback(error) {
                $log.log(error);
                $window.alert(error.data['error']);
            }); 
        }
    }
  ])
   .controller('TableController', ['$scope', '$log', '$http',
      function($scope, $log, $http) {
        $scope.isFavorite = false;
        $scope.table_uuid = '';

        $scope.favorite = function() {
          $scope.isFavorite = !$scope.isFavorite;

          $http.post('/favorite_table', {"favorite": $scope.isFavorite, "table_uuid": $scope.table_uuid}).
            then(function successCallback(response) {
            },
            function errorCallback(error) {
                $log.log(error);
            });
        }
    }
  ])
   .controller('ChartController', ['$scope', '$log', '$http',
      function($scope, $log, $http) {
        $scope.isFavorite = false;
        $scope.chart_uuid = '';

        $scope.favorite = function() {
          $scope.isFavorite = !$scope.isFavorite;

          $http.post('/favorite_chart', {"favorite": $scope.isFavorite, "chart_uuid": $scope.chart_uuid}).
            then(function successCallback(response) {
            },
            function errorCallback(error) {
                $log.log(error);
            });
        }
    }
  ]);

}());


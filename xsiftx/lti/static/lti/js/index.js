function update_task_list(response) {
  // Replace task list table with most updated version
  var table = ''
  for(var i=0; i < response.tasks.length; i++) {
	  var task = response.tasks[i]
	  table += '<tr id="tr-' + task.task_id + '"><td>' + task.sifter + '</td><td>' +
		  task.course + '</td><td>' + task.time + '</td><td>' + task.task_id + '</td>';
	  if(task.status == 'SIFTER_FAILURE') {
		  table += '<td><a href="#" id="a-' + task.task_id + '" class="failure_output">' +
			  task.status.toLowerCase() + '</td>';
	  } else {
		  table += '<td>' + task.status.toLowerCase() + '</td>'
	  }
	  table += '</tr>'

  }
  $('#tasks-table tbody').hide().html(table).fadeIn(300, function() {
	  for(var i=0; i < response.tasks.length; i++) {
		  var task = response.tasks[i]
		  if(task.status == 'SIFTER_FAILURE') {
			  // Highlight row
			  $('#tr-' + task.task_id).animate( { backgroundColor: '#ffcece' }, 500);
			  // Now create dialog click handlers
			  $('#a-' + task.task_id).click(function() {
				  $('<div><pre>' + $('<em></em>').text(task.results.error).html() + 
					'</pre></div>').dialog({
					  modal: true,
					  width: '70%',
					  buttons: {
						  Ok: function() {
							  $( this ).dialog( "close" );
						  }
					  }
				  });
			  });
		  }
	  }
  });

}

$(document).ready(function() {

  // Register click handlers for sifter actions
  $('button.sifter-run').click(function() {
	  var sifter_name = $(this).data('sifter')
	  $.ajax({
		  type: 'POST',
		  url: RUN_URL,
		  data: { sifter: sifter_name,
				  extra_args: $('#' + sifter_name + '-extra-args').val()
				},
		  dataType: 'json',
		  success: function(response) {
			  update_task_list(response);
		  },
		  error: function(request, status, error) {
			  var json = $.parseJSON(request.responseText);
			  $('div#run-error').html('Something has gone wrong with \
				 this request.  The server replied with a status of: '
				 + error + ' - ' + json.message);
		  }
	  });
  });

  // Click handler for updating status
  $('button#update-status').click(function() {
	  $.ajax({
		  type: 'PUT',
		  url: TASK_STATUS_URL,
		  dataType: 'json',
		  success: function(response) {
			  update_task_list(response)
		  },
		  error: function(request, status, error) {
			  var json = $.parseJSON(request.responseText);
			  $('div#run-error').html('Something has gone wrong with \
				 this request.  The server replied with a status of: '
				 + error + ' - ' + json.message);
		  }
	  });
  });

  // Click handler for removing old
  $('button#clear-tasks').click(function() {
	  $.ajax({
		  type: 'DELETE',
		  url: CLEAR_COMPLETE_TASKS_URL,
		  dataType: 'json',
		  success: function(response) {
			  update_task_list(response)
		  },
		  error: function(request, status, error) {
			  var json = $.parseJSON(request.responseText);
			  $('div#run-error').html('Something has gone wrong with \
				 this request.  The server replied with a status of: '
				 + error + ' - ' + json.message);
		  }
	  });
  });

  // Update the task table
  $.ajax({
	  type: 'PUT',
	  url: TASK_STATUS_URL,
	  dataType: 'json',
	  success: function(response) {
		  update_task_list(response)
	  },
	  error: function(request, status, error) {
		  var json = $.parseJSON(request.responseText);
		  $('div#run-error').html('Something has gone wrong with \
			this request.  The server replied with a status of: '
			+ error + ' - ' + json.message);
	  }
  });
});

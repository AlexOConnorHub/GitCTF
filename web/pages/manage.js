var toastElList = [].slice.call(document.querySelectorAll('.toast'))
var toastList = toastElList.map(function (toastEl) {
  return new bootstrap.Toast(toastEl)
})
$('#config-form-submit').on("click",
    function() {
        let individuals = 1;
        $.ajax({
            url: "/individuals",
            type: "GET",
            success: function(data){
                individuals = data;
                let teams = {};
                for (let individual in individuals) {
                    let team = individuals[individual].team;
                    if (teams[team] === undefined) {
                        teams[team] = [];
                    }
                    teams[team].push(individual);
                }
                $(".modal-body").html('<div class="row"></div>');
                let tableItemPartOne = '<tr><td id="team-member-name-label">';
                let tableItemPartTwo = '</td><td><button type="button" class="btn btn-danger" onclick="$(this).closest(\'tr\').remove();""><i class="fas fa-trash-alt"></i></button></td></tr>';
                let template = $(".template");
                for (let i = 1; i <= $("#number-of-teams").val(); i++) {
                    let card = template.find(".card").clone();
                    let team_key = "team-" + i;
                    console.log(team_key);
                    console.log(teams[team_key]);
                    if (teams[team_key] !== undefined) {
                        for (let j = 0; j < teams[team_key].length; j++) {
                            let name = teams[team_key][j];
                            let tableItem = tableItemPartOne + name + tableItemPartTwo;
                            card.find(".table").append(tableItem);
                            console.log(tableItem);
                            console.log(card.find(".table"));
                        }
                    }
                    card.find(".card-title").text("Team " + (i));
                    card.find(".btn").click(
                        function() {
                            let name = card.find("#team-member-name").val()
                            card.find(".table").last().append(tableItemPartOne + name + tableItemPartTwo);
                        }
                    );
                    $(".modal-body").children().append(card);
                }
                $(".modal").modal("show");
            }
        });
    }
);
$("#manage-submit-form").on( "click",
    function() {
        let data = new FormData($(".form-horizontal")[0]);
        $.ajax({
            type: "POST",
            url: $(".form-horizontal")[0].action,
            data: data,
            processData: false,
            contentType: false,
            success: function(data) {
                let myToast = bootstrap.Toast.getInstance($("#liveToast")[0]);
                $(".toast-body").text("Successfully updated config");
                $(".toast-body").addClass("text-success");
                myToast.show();
            },
            error: function(data) {
                let myToast = bootstrap.Toast.getInstance($("#liveToast")[0]);
                $(".toast-body").text("Error updating config");
                $(".toast-body").addClass("text-danger");
                myToast.show();
            }
        });
    }
);
$("#modal-submit").on(
    "click",
    function() {
        let data = new FormData($(".form-horizontal")[0]);
        let individuals = {};
        $(".modal-body").find(".card").each(
            function() {
                let team = $(this).find(".card-title").text().replace(" ", "-").toLowerCase();
                $(this).find(".table").find("tr").each(
                    function() {
                        let name = $(this).find("#team-member-name-label").text();
                        if (name !== "") {
                            individuals[name] = team;
                        }
                    }
                );
            }
        );
        console.log(individuals);
        data.append("individuals", JSON.stringify(individuals));
        $.ajax({
            type: "POST",
            url: "/individuals/update",
            data: data,
            processData: false,
            contentType: false,
            success: function(data) {
                window.location.href = "/manage";
            }
        });
    }
);
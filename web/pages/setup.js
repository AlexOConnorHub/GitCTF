$('#config-form-submit').on("click",
    function(){
        $(".modal-body").html('<div class="row justify-content-around"></div>');
        let tableItemPartOne = '<tr><td id="team-member-name-label">';
        let tableItemPartTwo = '</td><td><button type="button" class="btn btn-danger" onclick="$(this).closest(\'tr\').remove();""><i class="fas fa-trash-alt"></i></button></td></tr>';
        let template = $(".template");
        for (let i = 0; i < $("#number-of-teams").val(); i++) {
            let card = template.find(".card").clone();
            card.find(".card-title").text("Team " + (i+1));
            card.find(".btn").click(
                function() {
                    let name = card.find("#team-member-name").val()
                    $.ajax({
                        type: "GET",
                        url: "https://api.github.com/users/" + name,
                        success: (data) => {
                            card.find(".table").last().append(
                                tableItemPartOne + 
                                "<img src='" + data.avatar_url + "' width='50' height='50' class='rounded-circle'>" +
                                "<span style='margin-left: 10px;'></span>" +
                                name + 
                                tableItemPartTwo
                            );
                        },
                        error: (data) => {
                            card.find(".table").last().append(
                                tableItemPartOne +
                                name +
                                tableItemPartTwo
                            );
                        }
                    });
                }
            );
            $(".modal-body").children().append(card);
        }
        $(".modal").modal("show");
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
        data.append("individuals", JSON.stringify(individuals));
        $.ajax({
            type: "POST",
            url: $(".form-horizontal")[0].action,
            data: data,
            processData: false,
            contentType: false,
            success: function(data) {
                window.location.href = "/manage";
            }
        });
    }
);
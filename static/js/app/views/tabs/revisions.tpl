
<a href="<%= revisionURL %>" class="viewPlaceDetail bold">Revision JSON</a>
<p>Created at: <%= displayDate %> </p>
<!-- <p><%= digest %></p> -->
<% if (typeof(comment) != 'undefined') { %>
    <p><%= user %>: <%= comment %></p>
<% } %>
<p><span class="revertDisplay"><a href="" class="viewPlaceDetail buttonAdd revert">Revert <span><strong>&#8635;</strong></span></a></span><!-- <a href="" class="viewPlaceDetail viewDiff">View difference</a> --></p>

Jekyll::Hooks.register :documents, :pre_render do |doc|
  doc.content = doc.content.gsub(/\[([^\]]+)\]\(([^)]+)\)/) do |match|
    text   = $1
    target = $2

    # leave URLs, anchors, and already-correct /docs/ links alone
    next match if target =~ /\Ahttps?:\/\//
    next match if target.start_with?("#")
    next match if target.start_with?("/docs/")

    # split off anchor
    path, anchor = target.split("#", 2)

    # decode URL encoding and strip relative traversal + extension
    path = URI.decode_www_form_component(path)
    path = File.basename(path, ".*")   # "../../Network & Services/background-services" → "background-services"

    permalink = "/docs/#{path}/"
    permalink += "##{anchor}" if anchor

    "[#{text}](#{permalink})"
  end
end

require "uri"
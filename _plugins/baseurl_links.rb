# Prefix generated root-relative site URLs with the configured Pages baseurl.
#
# Synced upstream docs intentionally use canonical paths such as /docs/... and
# /assets/external-docs/.... Those paths work at localhost root, but project
# Pages deployments are served below a repository base path.
module AnyLogBaseurlLinks
  def self.rewrite(item)
    return unless item.respond_to?(:output_ext) && item.output_ext == ".html"

    baseurl = item.site.config["baseurl"].to_s
    return if baseurl.empty? || baseurl == "/"

    baseurl = "/" + baseurl.sub(%r{\A/+}, "").sub(%r{/+\z}, "")
    prefixes = %w[/docs/ /assets/ /search-index.json /feed.xml /sitemap.xml]

    item.output = item.output.gsub(
      /(?<attr>\b(?:href|src|poster|data)=["'])(?<url>\/(?:docs\/|assets\/|search-index\.json|feed\.xml|sitemap\.xml)[^"']*)(?<quote>["'])/
    ) do
      attr = Regexp.last_match[:attr]
      url = Regexp.last_match[:url]
      quote = Regexp.last_match[:quote]

      if prefixes.any? { |prefix| url == prefix || url.start_with?(prefix) } && !url.start_with?(baseurl + "/")
        "#{attr}#{baseurl}#{url}#{quote}"
      else
        "#{attr}#{url}#{quote}"
      end
    end
  end
end

Jekyll::Hooks.register :pages, :post_render do |item|
  AnyLogBaseurlLinks.rewrite(item)
end

Jekyll::Hooks.register :documents, :post_render do |item|
  AnyLogBaseurlLinks.rewrite(item)
end

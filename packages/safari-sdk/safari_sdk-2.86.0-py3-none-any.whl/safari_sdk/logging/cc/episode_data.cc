#include "third_party/safari/sdk/safari/logging/cc/episode_data.h"

#include <cstdint>
#include <memory>
#include <utility>
#include <vector>

#include "third_party/absl/memory/memory.h"
#include "third_party/absl/status/status.h"
#include "third_party/absl/status/statusor.h"
#include "third_party/absl/strings/str_cat.h"
#include "third_party/absl/strings/string_view.h"

namespace safari::logging {

absl::StatusOr<std::unique_ptr<EpisodeData>> EpisodeData::Create(
    std::unique_ptr<EpisodeDataPayloadInterface> payload,
    std::vector<int64_t> timestamps) {
  return absl::WrapUnique(
      new EpisodeData(std::move(payload), std::move(timestamps)));
}

absl::Status EpisodeData::InsertBuffer(absl::string_view key,
                                       EpisodeFeatureBufferVariant buffer) {
  auto [it, inserted] = data_map_.try_emplace(key, std::move(buffer));
  if (!inserted) {
    return absl::AlreadyExistsError(
        absl::StrCat("The key: ", key,
                     " already exists in the data map. Therefore, the data "
                     "could not be inserted."));
  }
  return absl::OkStatus();
}

}  // namespace safari::logging

#ifndef THIRD_PARTY_SAFARI_SDK_SAFARI_LOGGING_CC_MCAP_WRITE_OP_H_
#define THIRD_PARTY_SAFARI_SDK_SAFARI_LOGGING_CC_MCAP_WRITE_OP_H_

#include <cstdint>
#include <string>

#include "third_party/protobuf/descriptor.h"

namespace safari::logging {

// This struct is used to encapsulate the information required to write a
// message to an MCAP file.
struct McapWriteOp {
  // In the format: episode_<episode_uuid>
  std::string filename_prefix;
  // Serialized tensorflow.Example or safari.protos.logging.Session proto.
  std::string serialized_message;
  // The message descriptor of the serialized proto message.
  const proto2::Descriptor* descriptor;
  // Topic to write the message to.
  std::string topic;
  // Observation timestamp of the raw data in nanoseconds.
  // This is important for ordering the data in SSOT.
  int64_t publish_time_ns;
  // Log timestamp of the raw data in nanoseconds.
  int64_t log_time_ns;
};

// Configuration for creating an MCAP file.
struct McapFileConfig {
  // The output directory for the MCAP files.
  // The files will be written to a subdirectory of this directory.
  std::string output_dir;
  // The topic to use when writing the file metadata proto.
  std::string file_metadata_topic;
  // The agent id to use when writing the file metadata proto.
  std::string agent_id;
  // The maximum size of a single MCAP file in bytes.
  // If a message is larger than this size, it will be written to a new file.
  int64_t file_shard_size_limit_bytes;
};

}  // namespace safari::logging

#endif  // THIRD_PARTY_SAFARI_SDK_SAFARI_LOGGING_CC_MCAP_WRITE_OP_H_
